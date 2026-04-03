"""Tests for the RAG engine (RigorousRAGEngine)."""

from unittest.mock import MagicMock, patch

import pytest

from cerebro.core.rag.engine import RigorousRAGEngine
from cerebro.interfaces.llm import LLMProvider
from cerebro.interfaces.vector_store import VectorStoreProvider


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
        persist_directory="./test_db",
    )
    assert engine.persist_directory == "./test_db"
    assert engine.llm_provider == mock_llm_provider
    assert engine.vector_store_provider == mock_vector_store_provider


def test_initialization_with_local_defaults(monkeypatch):
    """Test local-first default provider selection."""
    monkeypatch.delenv("CEREBRO_LLM_PROVIDER", raising=False)
    with patch("cerebro.core.rag.engine.LlamaCppProvider") as mock_llama:
        with patch("cerebro.core.rag.engine.ChromaVectorStoreProvider") as mock_chroma:
            engine = RigorousRAGEngine(persist_directory="./test_db")
            assert engine.persist_directory == "./test_db"
            mock_llama.assert_called_once()
            mock_chroma.assert_called_once()


def test_provider_alias_resolution_uses_registered_aliases(monkeypatch):
    """Test explicit alias resolution for the configured provider."""
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "llama.cpp")
    with patch("cerebro.core.rag.engine.LlamaCppProvider") as mock_llama:
        with patch("cerebro.core.rag.engine.ChromaVectorStoreProvider"):
            RigorousRAGEngine(persist_directory="./test_db")
    mock_llama.assert_called_once()


def test_provider_alias_resolution_rejects_ambiguous_values(monkeypatch):
    """Test that unregistered aliases are rejected."""
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "local")
    with pytest.raises(ValueError, match="Supported aliases"):
        RigorousRAGEngine(
            llm_provider=None,
            vector_store_provider=MagicMock(spec=VectorStoreProvider),
            persist_directory="./test_db",
        )


def test_ingest_file_not_found(mock_llm_provider, mock_vector_store_provider):
    """Test ingest with non-existent file."""
    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider,
    )
    with pytest.raises(FileNotFoundError):
        engine.ingest("non_existent_file.jsonl")


def test_ingest_local_success(tmp_path, mock_llm_provider, mock_vector_store_provider):
    """Test local ingestion into the vector store."""
    jsonl_path = tmp_path / "artifacts.jsonl"
    jsonl_path.write_text(
        '{"jsonData": "{\\"title\\": \\"test\\", \\"content\\": \\"code content\\", \\"repo\\": \\"repo1\\"}"}\n',
        encoding="utf-8",
    )

    mock_llm_provider.embed_batch.return_value = [[0.1, 0.2, 0.3]]
    mock_vector_store_provider.add_documents.return_value = 1

    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider,
    )

    count = engine.ingest(str(jsonl_path))

    assert count == 1
    mock_llm_provider.embed_batch.assert_called_once_with(["code content"])
    mock_vector_store_provider.add_documents.assert_called_once()


def test_query_with_metrics_no_local_data(mock_llm_provider, mock_vector_store_provider):
    """Test query when no local vector data is available."""
    mock_llm_provider.grounded_generate.return_value = {
        "answer": "No answer could be generated from the available context.",
        "citations": [],
        "confidence": 0.0,
        "cost_estimate": 0.0,
    }

    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider,
    )

    result = engine.query_with_metrics("test query")

    assert "No answer" in result["answer"]
    assert result["error"] is False
    assert result["metrics"]["avg_confidence"] == 0.0
    assert "0/5" in result["metrics"]["hit_rate_k"]
    mock_llm_provider.grounded_generate.assert_called_once_with(
        query="test query",
        context=[],
        top_k=5,
    )


def test_query_with_metrics_uses_local_context(mock_llm_provider, mock_vector_store_provider):
    """Test successful local retrieval and grounded generation."""
    mock_vector_store_provider.get_document_count.return_value = 1
    mock_llm_provider.embed.return_value = [0.9, 0.1]
    mock_vector_store_provider.search.return_value = [
        {
            "id": "doc_1",
            "content": "def hello():\n    print('world')",
            "metadata": {"source": "repo/main.py"},
            "similarity": 0.95,
        }
    ]
    mock_llm_provider.grounded_generate.return_value = {
        "answer": "The hello function prints world.",
        "citations": ["[1]"],
        "confidence": 0.95,
        "cost_estimate": 0.0,
        "snippets": ["def hello():\n    print('world')"],
    }

    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider,
    )

    result = engine.query_with_metrics("What does hello do?")

    assert "hello" in result["answer"]
    assert result["error"] is False
    assert result["metrics"]["avg_confidence"] == 0.95
    assert result["metrics"]["citations"] == ["repo/main.py"]
    assert "1/5" in result["metrics"]["hit_rate_k"]
    mock_llm_provider.embed.assert_called_once_with("What does hello do?")
    mock_vector_store_provider.search.assert_called_once_with([0.9, 0.1], top_k=5)
    mock_llm_provider.grounded_generate.assert_called_once_with(
        query="What does hello do?",
        context=["def hello():\n    print('world')"],
        top_k=5,
    )
