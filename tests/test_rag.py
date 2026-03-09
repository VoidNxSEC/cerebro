"""Tests for the RAG engine (RigorousRAGEngine).

All GCP/chromadb imports are mocked to allow running locally.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, mock_open

# Mock heavy dependencies at import time so the module loads cleanly.
# Must cover the full import chain that engine.py triggers:
#   engine -> vertex_ai_llm -> google.cloud.discoveryengine_v1beta, google.auth
#   engine -> chroma_vector_store (chromadb is lazy-imported inside __init__, OK)
_GCP_MOCKS = {
    "google": MagicMock(),
    "google.cloud": MagicMock(),
    "google.cloud.storage": MagicMock(),
    "google.cloud.discoveryengine_v1beta": MagicMock(),
    "google.api_core": MagicMock(),
    "google.api_core.exceptions": MagicMock(),
    "google.auth": MagicMock(),
    "google.auth.credentials": MagicMock(),
    "langchain_google_vertexai": MagicMock(),
}

with patch.dict("sys.modules", _GCP_MOCKS):
    from phantom.core.rag import engine as _rag_engine_mod
    RigorousRAGEngine = _rag_engine_mod.RigorousRAGEngine

from phantom.interfaces.llm import LLMProvider
from phantom.interfaces.vector_store import VectorStoreProvider


@pytest.fixture
def mock_llm_provider():
    """Mock LLMProvider for testing."""
    mock = MagicMock(spec=LLMProvider)
    mock.health_check.return_value = True
    return mock


@pytest.fixture
def mock_vector_store_provider():
    """Mock VectorStoreProvider for testing."""
    mock = MagicMock(spec=VectorStoreProvider)
    mock.health_check.return_value = True
    mock.get_document_count.return_value = 0
    return mock


def test_initialization(mock_llm_provider, mock_vector_store_provider):
    """Test RAG engine initialization with provider injection."""
    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider,
        persist_directory="./test_db"
    )
    assert engine.persist_directory == "./test_db"
    assert engine.llm_provider == mock_llm_provider
    assert engine.vector_store_provider == mock_vector_store_provider


def test_initialization_with_defaults():
    """Test RAG engine initialization with default providers."""
    with patch.object(_rag_engine_mod, "VertexAILLMProvider") as mock_vertex:
        with patch.object(_rag_engine_mod, "ChromaVectorStoreProvider") as mock_chroma:
            engine = RigorousRAGEngine(persist_directory="./test_db")
            assert engine.persist_directory == "./test_db"
            mock_vertex.assert_called_once()
            mock_chroma.assert_called_once()


def test_ingest_file_not_found(mock_llm_provider, mock_vector_store_provider):
    """Test ingest with non-existent file."""
    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider,
        data_store_id="test-store",
    )
    engine.project_id = "test-project"
    with pytest.raises(FileNotFoundError):
        engine.ingest("non_existent_file.jsonl")


@patch("builtins.open", new_callable=mock_open, read_data='{"jsonData": "{\\"title\\": \\"test\\", \\"content\\": \\"code content\\", \\"repo\\": \\"repo1\\"}"}\n')
@patch.object(_rag_engine_mod, "Path")
@patch.object(_rag_engine_mod, "storage")
def test_ingest_success(mock_storage_mod, mock_path_cls, mock_file):
    """Test successful ingestion with mocked providers."""
    mock_path_cls.return_value.exists.return_value = True
    mock_bucket = MagicMock()
    mock_storage_mod.Client.return_value.get_bucket.return_value = mock_bucket

    # Use a plain MagicMock (no spec) since import_documents isn't on LLMProvider ABC
    llm = MagicMock()
    llm.import_documents.return_value = "operation-123"
    vs = MagicMock()

    engine = RigorousRAGEngine(
        llm_provider=llm,
        vector_store_provider=vs,
        data_store_id="test-store"
    )
    engine.project_id = "test-project"

    count = engine.ingest("test.jsonl")

    assert count > 0
    llm.import_documents.assert_called_once()


def test_query_with_metrics_no_data(mock_llm_provider, mock_vector_store_provider):
    """Test query when no data is available."""
    mock_llm_provider.grounded_generate.return_value = {
        "answer": "No answer could be generated from the available context.",
        "citations": [],
        "confidence": 0.0,
        "cost_estimate": 0.0,
    }

    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider
    )

    result = engine.query_with_metrics("test query")

    assert "No answer" in result["answer"]
    assert result["error"] is False
    assert result["metrics"]["avg_confidence"] == 0.0
    assert "0/5" in result["metrics"]["hit_rate_k"]


def test_query_with_metrics_success(mock_llm_provider, mock_vector_store_provider):
    """Test successful query with grounded generation."""
    mock_llm_provider.grounded_generate.return_value = {
        "answer": "The hello function prints world.",
        "citations": ["repo/file.py"],
        "confidence": 0.95,
        "cost_estimate": 0.004,
    }

    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider
    )

    result = engine.query_with_metrics("What does hello do?")

    assert "hello" in result["answer"]
    assert result["error"] is False
    assert result["metrics"]["avg_confidence"] == 0.95
    assert "1/5" in result["metrics"]["hit_rate_k"]
    assert len(result["metrics"]["citations"]) > 0
