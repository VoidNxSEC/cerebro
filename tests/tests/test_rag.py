
import json
import pytest
from unittest.mock import MagicMock, patch, mock_open
from phantom.core.rag.engine import RigorousRAGEngine
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
    # This will use real providers, so we patch them
    with patch("phantom.providers.gcp.vertex_ai_llm.VertexAILLMProvider") as mock_vertex:
        with patch("phantom.providers.chroma.chroma_vector_store.ChromaVectorStoreProvider") as mock_chroma:
            engine = RigorousRAGEngine(persist_directory="./test_db")
            assert engine.persist_directory == "./test_db"
            # Verify default providers were instantiated
            mock_vertex.assert_called_once()
            mock_chroma.assert_called_once()


def test_ingest_file_not_found(mock_llm_provider, mock_vector_store_provider):
    """Test ingest with non-existent file."""
    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider
    )
    with pytest.raises(FileNotFoundError):
        engine.ingest("non_existent_file.jsonl")


@patch("builtins.open", new_callable=mock_open, read_data='{"jsonData": "{\\"title\\": \\"test\\", \\"content\\": \\"code content\\", \\"repo\\": \\"repo1\\"}"}\n')
@patch("phantom.core.rag.engine.Path.exists", return_value=True)
@patch("phantom.core.rag.engine.storage.Client")
def test_ingest_success(mock_storage, mock_exists, mock_file, mock_llm_provider, mock_vector_store_provider):
    """Test successful ingestion with mocked providers."""
    # Mock GCS storage
    mock_bucket = MagicMock()
    mock_storage.return_value.get_bucket.return_value = mock_bucket
    
    # Mock LLM provider import
    mock_llm_provider.import_documents.return_value = "operation-123"
    
    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider,
        data_store_id="test-store"
    )
    engine.project_id = "test-project"
    
    count = engine.ingest("test.jsonl")
    
    assert count > 0
    mock_llm_provider.import_documents.assert_called_once()


def test_query_with_metrics_no_data(mock_llm_provider, mock_vector_store_provider):
    """Test query when no data is available."""
    # Mock empty grounded generation response
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
    assert result["metrics"]["avg_confidence"] == 0.0
    assert result["metrics"]["hit_rate_k"] == "0%"


def test_query_with_metrics_success(mock_llm_provider, mock_vector_store_provider):
    """Test successful query with grounded generation."""
    # Mock successful grounded generation response
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
    assert result["metrics"]["avg_confidence"] == 0.95
    assert result["metrics"]["hit_rate_k"] == "100%"
    assert len(result["metrics"]["citations"]) > 0
