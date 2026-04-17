"""Tests for the RAG engine (RigorousRAGEngine)."""

import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from cerebro.core.rag.embeddings import EmbeddingResult, EmbeddingSystem
from cerebro.core.rag.engine import RigorousRAGEngine, get_rag_runtime_status_snapshot
from cerebro.interfaces.llm import LLMProvider
from cerebro.interfaces.vector_store import (
    StoredVectorDocument,
    VectorSearchResult,
    VectorStoreHealth,
    VectorStoreProvider,
)
from cerebro.settings import reset_settings_cache


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
    mock.backend_name = "mock-store"
    mock.health_check.return_value = True
    mock.get_document_count.return_value = 0
    mock.health_status.return_value = VectorStoreHealth(
        healthy=True,
        backend="mock-store",
        details={
            "collection_name": "test_collection",
            "default_namespace": "test-namespace",
        },
    )
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
    reset_settings_cache()
    with patch("cerebro.core.rag.engine.LlamaCppProvider") as mock_llama:
        with patch("cerebro.core.rag.engine.build_vector_store_provider") as mock_vector_store:
            engine = RigorousRAGEngine(persist_directory="./test_db")
            assert engine.persist_directory == "./test_db"
            mock_llama.assert_called_once()
            mock_vector_store.assert_called_once()


def test_provider_alias_resolution_uses_registered_aliases(monkeypatch):
    """Test explicit alias resolution for the configured provider."""
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "llama.cpp")
    reset_settings_cache()
    with patch("cerebro.core.rag.engine.LlamaCppProvider") as mock_llama:
        with patch("cerebro.core.rag.engine.build_vector_store_provider"):
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
    """Test local ingestion uses EmbeddingSystem (not llm_provider) for embeddings."""
    jsonl_path = tmp_path / "artifacts.jsonl"
    jsonl_path.write_text(
        '{"jsonData": "{\\"title\\": \\"test\\", \\"content\\": \\"code content\\", \\"repo\\": \\"repo1\\"}"}\n',
        encoding="utf-8",
    )

    mock_vector_store_provider.upsert_documents.return_value = 1

    with patch("cerebro.core.rag.engine.EmbeddingSystem") as mock_embed_cls:
        mock_embed = MagicMock()
        mock_embed.embed.return_value = EmbeddingResult(
            vectors=[[0.1, 0.2, 0.3]], model_used="test", dimension=3, latency_ms=0.0, batch_size=1
        )
        mock_embed_cls.return_value = mock_embed

        engine = RigorousRAGEngine(
            llm_provider=mock_llm_provider,
            vector_store_provider=mock_vector_store_provider,
        )

        count = engine.ingest(str(jsonl_path))

    assert count == 1
    mock_embed.embed.assert_called_once_with(["code content"])
    mock_llm_provider.embed_batch.assert_not_called()
    mock_vector_store_provider.upsert_documents.assert_called_once_with(
        [
            {
                "id": "repo1:test:1",
                "content": "code content",
                "title": "test",
                "repo": "repo1",
                "source": "repo1/test",
            }
        ],
        [[0.1, 0.2, 0.3]],
        namespace=None,
    )


def test_query_with_metrics_no_local_data(mock_llm_provider, mock_vector_store_provider):
    """Test query when no local vector data is available."""

    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider,
    )

    result = engine.query_with_metrics("test query")

    assert "No relevant information found" in result["answer"]
    assert result["error"] is False
    assert result["metrics"]["avg_confidence"] == 0.0
    assert "0/5" in result["metrics"]["hit_rate_k"]
    assert result["metrics"]["grounded"] is False
    mock_llm_provider.grounded_generate.assert_not_called()


def test_query_with_metrics_uses_local_context(mock_llm_provider, mock_vector_store_provider):
    """Test that local retrieval uses EmbeddingSystem (not llm_provider) for query embedding."""
    from unittest.mock import MagicMock

    mock_vector_store_provider.get_document_count.return_value = 1
    mock_vector_store_provider.search.return_value = [
        VectorSearchResult(
            id="doc_1",
            content="def hello():\n    print('world')",
            metadata={"source": "repo/main.py"},
            score=0.95,
            source="repo/main.py",
        )
    ]
    mock_llm_provider.grounded_generate.return_value = {
        "answer": "The hello function prints world.",
        "citations": ["[1]"],
        "confidence": 0.95,
        "cost_estimate": 0.0,
        "snippets": ["def hello():\n    print('world')"],
    }

    with patch("cerebro.core.rag.engine.EmbeddingSystem") as mock_embed_cls:
        mock_embed = MagicMock()
        mock_embed.embed_query.return_value = [0.9, 0.1]
        mock_embed_cls.return_value = mock_embed

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
    mock_embed.embed_query.assert_called_once_with("What does hello do?")
    mock_llm_provider.embed.assert_not_called()
    mock_vector_store_provider.search.assert_called_once_with(
        [0.9, 0.1],
        top_k=5,
        namespace=None,
    )
    mock_llm_provider.grounded_generate.assert_called_once_with(
        query="What does hello do?",
        context=["def hello():\n    print('world')"],
        top_k=5,
    )


def test_embedding_system_uses_project_local_cache_dir(tmp_path, monkeypatch):
    """Embedding downloads should stay in a writable local cache."""

    cache_root = tmp_path / "models"
    monkeypatch.setenv("CEREBRO_MODEL_CACHE_DIR", str(cache_root))
    EmbeddingSystem.clear_cache()

    fake_sentence_transformer = MagicMock(name="SentenceTransformer")
    fake_module = SimpleNamespace(SentenceTransformer=fake_sentence_transformer)

    with patch.dict(sys.modules, {"sentence_transformers": fake_module}):
        system = EmbeddingSystem(strategy="code", device="cpu")
        resolved_model_name, _ = system._load_model("sentence-transformers/all-MiniLM-L6-v2")

    expected_cache_folder = cache_root / "sentence-transformers"
    assert resolved_model_name == "sentence-transformers/all-MiniLM-L6-v2"
    fake_sentence_transformer.assert_called_once_with(
        "sentence-transformers/all-MiniLM-L6-v2",
        device="cpu",
        cache_folder=str(expected_cache_folder),
    )
    assert os.environ["HF_HOME"] == str(cache_root / "huggingface")
    assert os.environ["SENTENCE_TRANSFORMERS_HOME"] == str(expected_cache_folder)
    assert expected_cache_folder.exists()


def test_embedding_system_marks_incompatible_model_unavailable(tmp_path, monkeypatch):
    """A failed preferred model should not be retried on subsequent loads."""

    cache_root = tmp_path / "models"
    monkeypatch.setenv("CEREBRO_MODEL_CACHE_DIR", str(cache_root))
    EmbeddingSystem.clear_cache()

    fallback_model = MagicMock(name="fallback_model")
    fallback_model.encode.return_value = MagicMock(tolist=lambda: [[0.1, 0.2]])
    load_attempts: list[str] = []

    def fake_sentence_transformer(model_name: str, **kwargs):
        load_attempts.append(model_name)
        if model_name == "jinaai/jina-embeddings-v2-base-code":
            raise RuntimeError("unsupported attention backend")
        return fallback_model

    fake_module = SimpleNamespace(SentenceTransformer=fake_sentence_transformer)

    with patch.dict(sys.modules, {"sentence_transformers": fake_module}):
        system = EmbeddingSystem(strategy="code", device="cpu")
        first_model_name, first_model = system._load_model("jinaai/jina-embeddings-v2-base-code")
        second_model_name, second_model = system._load_model("jinaai/jina-embeddings-v2-base-code")

    assert first_model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert second_model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert first_model is fallback_model
    assert second_model is fallback_model
    assert load_attempts == [
        "jinaai/jina-embeddings-v2-base-code",
        "sentence-transformers/all-MiniLM-L6-v2",
    ]


def test_embedding_system_reuses_same_model_for_query_and_documents(tmp_path, monkeypatch):
    """Document and query embeddings must stay in the same vector space."""

    cache_root = tmp_path / "models"
    monkeypatch.setenv("CEREBRO_MODEL_CACHE_DIR", str(cache_root))
    EmbeddingSystem.clear_cache()

    load_attempts: list[str] = []

    class FakeEncodedBatch:
        def __init__(self, rows: list[list[float]]):
            self._rows = rows

        def tolist(self) -> list[list[float]]:
            return self._rows

    class FakeModel:
        def __init__(self, dimension: int):
            self.dimension = dimension

        def encode(self, batch, **kwargs):
            return FakeEncodedBatch([[0.1] * self.dimension for _ in batch])

    def fake_sentence_transformer(model_name: str, **kwargs):
        load_attempts.append(model_name)
        if model_name == "jinaai/jina-embeddings-v2-base-code":
            raise RuntimeError("unsupported attention backend")
        if model_name == "sentence-transformers/all-MiniLM-L6-v2":
            return FakeModel(384)
        if model_name == "sentence-transformers/all-mpnet-base-v2":
            return FakeModel(768)
        raise AssertionError(f"Unexpected model load: {model_name}")

    fake_module = SimpleNamespace(SentenceTransformer=fake_sentence_transformer)

    with patch.dict(sys.modules, {"sentence_transformers": fake_module}):
        system = EmbeddingSystem(strategy="code", device="cpu")
        document_result = system.embed(["def hello(): pass"], content_type="code")
        query_vector = system.embed_query("What does hello do?")

    assert document_result.dimension == 384
    assert len(query_vector) == 384
    assert load_attempts == [
        "jinaai/jina-embeddings-v2-base-code",
        "sentence-transformers/all-MiniLM-L6-v2",
    ]


def test_embedding_system_suppresses_vendor_bootstrap_output(tmp_path, monkeypatch, capsys):
    """Third-party model bootstrap noise should not leak into CLI output."""

    cache_root = tmp_path / "models"
    monkeypatch.setenv("CEREBRO_MODEL_CACHE_DIR", str(cache_root))
    monkeypatch.delenv("CEREBRO_VERBOSE_MODEL_LOAD", raising=False)
    EmbeddingSystem.clear_cache()

    def noisy_sentence_transformer(model_name: str, **kwargs):
        print("vendor stdout noise")
        print("vendor stderr noise", file=sys.stderr)
        return MagicMock(name="model")

    fake_module = SimpleNamespace(SentenceTransformer=noisy_sentence_transformer)

    with patch.dict(sys.modules, {"sentence_transformers": fake_module}):
        system = EmbeddingSystem(strategy="code", device="cpu")
        system._load_model("sentence-transformers/all-MiniLM-L6-v2")

    captured = capsys.readouterr()
    assert "vendor stdout noise" not in captured.out
    assert "vendor stderr noise" not in captured.err


def test_get_runtime_status_reports_backend_metadata(
    mock_llm_provider,
    mock_vector_store_provider,
):
    """Test runtime status output for the provider-based RAG engine."""

    mock_vector_store_provider.get_document_count.return_value = 12

    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider,
        vector_store_namespace="prod",
        vector_store_collection_name="documents",
    )

    status = engine.get_runtime_status()

    assert status["healthy"] is True
    assert status["mode"] == "local"
    assert status["backend"] == "mock-store"
    assert status["llm_provider"] == "LLMProvider"
    assert status["namespace"] == "test-namespace"
    assert status["collection_name"] == "test_collection"
    assert status["document_count"] == 12


def test_get_runtime_status_marks_backend_unhealthy_on_count_error(
    mock_llm_provider,
    mock_vector_store_provider,
):
    """Document count failures should propagate into runtime health output."""

    mock_vector_store_provider.get_document_count.side_effect = RuntimeError("vector store offline")

    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider,
    )

    status = engine.get_runtime_status()

    assert status["healthy"] is False
    assert status["document_count"] is None
    assert status["error"] == "vector store offline"


def test_run_smoke_test_performs_write_read_cleanup(
    mock_llm_provider,
    mock_vector_store_provider,
):
    """Smoke test should validate write/read/delete on the active backend."""

    mock_vector_store_provider.get_document_count.return_value = 4
    mock_vector_store_provider.search.return_value = [
        VectorSearchResult(
            id="__cerebro_smoke__:match",
            content="smoke content",
            metadata={"source": "cerebro://smoke"},
            score=0.99,
        )
    ]
    mock_vector_store_provider.delete_documents.return_value = 1

    with patch("cerebro.core.rag.engine.uuid4") as mock_uuid4:
        mock_uuid4.side_effect = [MagicMock(hex="source"), MagicMock(hex="match")]
        with patch("cerebro.core.rag.engine.EmbeddingSystem") as mock_embed_cls:
            mock_embed = MagicMock()
            mock_embed.embed.return_value = EmbeddingResult(
                vectors=[[0.1, 0.2]],
                model_used="test",
                dimension=2,
                latency_ms=0.0,
                batch_size=1,
            )
            mock_embed.embed_query.return_value = [0.1, 0.2]
            mock_embed_cls.return_value = mock_embed

            engine = RigorousRAGEngine(
                llm_provider=mock_llm_provider,
                vector_store_provider=mock_vector_store_provider,
            )
            result = engine.run_smoke_test()

    assert result["healthy"] is True
    assert result["query_hits"] == 1
    mock_vector_store_provider.initialize_schema.assert_called_once_with()
    mock_vector_store_provider.upsert_documents.assert_called_once()
    mock_vector_store_provider.delete_documents.assert_called_once()


def test_migrate_documents_exports_and_upserts_batches(
    mock_llm_provider,
    mock_vector_store_provider,
):
    """Migration should batch-export from the source provider and upsert into the destination."""

    source_provider = MagicMock(spec=VectorStoreProvider)
    source_provider.backend_name = "chroma"
    source_provider.get_document_count.return_value = 2
    source_provider.export_documents.side_effect = [
        [
            StoredVectorDocument(
                id="doc-1",
                content="alpha",
                metadata={"title": "Alpha", "source": "repo/a.py"},
                embedding=[0.1, 0.2],
            ),
            StoredVectorDocument(
                id="doc-2",
                content="beta",
                metadata={"title": "Beta", "source": "repo/b.py"},
                embedding=[0.3, 0.4],
            ),
        ],
        [],
    ]
    mock_vector_store_provider.get_document_count.side_effect = [3, 5]
    mock_vector_store_provider.upsert_documents.return_value = 2

    engine = RigorousRAGEngine(
        llm_provider=mock_llm_provider,
        vector_store_provider=mock_vector_store_provider,
    )

    result = engine.migrate_documents(source_provider, batch_size=50, clear_destination=True)

    assert result["source_backend"] == "chroma"
    assert result["destination_backend"] == "mock-store"
    assert result["migrated_count"] == 2
    assert result["destination_count_before"] == 3
    assert result["destination_count_after"] == 5
    mock_vector_store_provider.clear.assert_called_once_with(namespace=None)
    mock_vector_store_provider.upsert_documents.assert_called_once()
    source_provider.export_documents.assert_any_call(namespace=None, limit=50, offset=0)


def test_runtime_status_snapshot_falls_back_when_engine_init_fails(monkeypatch):
    """The shared snapshot helper should still return a typed payload on init errors."""

    monkeypatch.setenv("CEREBRO_VECTOR_STORE_PROVIDER", "chromadb")
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_COLLECTION_NAME", "prod_collection")
    monkeypatch.setenv("CEREBRO_LLM_PROVIDER", "llamacpp")
    reset_settings_cache()

    with patch("cerebro.core.rag.engine.RigorousRAGEngine", side_effect=RuntimeError("boom")):
        status = get_rag_runtime_status_snapshot()

    assert status["healthy"] is False
    assert status["mode"] == "unavailable"
    assert status["backend"] == "chromadb"
    assert status["collection_name"] == "prod_collection"
    assert status["error"] == "boom"
