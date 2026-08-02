"""Tests for the provider-based KnowledgeIndexer."""

from unittest.mock import MagicMock, patch

from cerebro.core.rag.embeddings import EmbeddingResult
from cerebro.intelligence.core import (
    CerebroIntelligence,
    IntelligenceItem,
    IntelligenceType,
    ThreatLevel,
)
from cerebro.interfaces.vector_store import VectorSearchResult, VectorStoreProvider
from cerebro.registry.indexer import KnowledgeIndexer


def _build_intelligence_item(
    item_id: str,
    title: str,
    content: str,
    intel_type: IntelligenceType,
    projects: list[str],
) -> IntelligenceItem:
    return IntelligenceItem(
        id=item_id,
        type=intel_type,
        source=f"{projects[0] if projects else 'unknown'}/source",
        title=title,
        content=content,
        threat_level=ThreatLevel.INFO,
        tags=["test"],
        related_projects=projects,
    )


def test_index_all_uses_upsert_and_returns_new_document_count(tmp_path):
    cerebro = CerebroIntelligence(
        arch_path=str(tmp_path / "arch"),
        data_dir=str(tmp_path / "data"),
    )
    cerebro.add_intelligence(
        _build_intelligence_item(
            "intel-1",
            "Alpha",
            "alpha content",
            IntelligenceType.TECHINT,
            ["alpha"],
        )
    )
    cerebro.add_intelligence(
        _build_intelligence_item(
            "intel-2",
            "Beta",
            "beta content",
            IntelligenceType.OSINT,
            ["beta"],
        )
    )

    provider = MagicMock(spec=VectorStoreProvider)
    provider.backend_name = "pgvector"
    provider.get_document_count.side_effect = [1, 3]

    with patch("cerebro.registry.indexer.EmbeddingSystem") as mock_embedding_cls:
        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = EmbeddingResult(
            vectors=[[0.1, 0.2], [0.2, 0.3]],
            model_used="test",
            dimension=2,
            latency_ms=0.0,
            batch_size=2,
        )
        mock_embedding_cls.return_value = mock_embedding

        indexer = KnowledgeIndexer(cerebro, vector_store_provider=provider)
        indexed = indexer.index_all()

    assert indexed == 2
    provider.initialize_schema.assert_called_once_with()
    provider.upsert_documents.assert_called_once()
    documents, embeddings = provider.upsert_documents.call_args.args[:2]
    assert len(documents) == 2
    assert len(embeddings) == 2


def test_semantic_query_applies_type_and_project_filters(tmp_path):
    cerebro = CerebroIntelligence(
        arch_path=str(tmp_path / "arch"),
        data_dir=str(tmp_path / "data"),
    )
    alpha = _build_intelligence_item(
        "intel-alpha",
        "Alpha finding",
        "alpha content",
        IntelligenceType.TECHINT,
        ["alpha"],
    )
    beta = _build_intelligence_item(
        "intel-beta",
        "Beta finding",
        "beta content",
        IntelligenceType.OSINT,
        ["beta"],
    )
    shared = _build_intelligence_item(
        "intel-shared",
        "Shared finding",
        "shared content",
        IntelligenceType.TECHINT,
        ["alpha", "beta"],
    )
    for item in (alpha, beta, shared):
        cerebro.add_intelligence(item)

    provider = MagicMock(spec=VectorStoreProvider)
    provider.backend_name = "pgvector"
    provider.get_document_count.return_value = 3
    provider.search.return_value = [
        VectorSearchResult(id=alpha.id, content=alpha.content, metadata={}, score=0.99),
        VectorSearchResult(id=beta.id, content=beta.content, metadata={}, score=0.98),
        VectorSearchResult(id=shared.id, content=shared.content, metadata={}, score=0.97),
    ]

    with patch("cerebro.registry.indexer.EmbeddingSystem") as mock_embedding_cls:
        mock_embedding = MagicMock()
        mock_embedding.embed_query.return_value = [0.4, 0.6]
        mock_embedding_cls.return_value = mock_embedding

        indexer = KnowledgeIndexer(cerebro, vector_store_provider=provider)
        results = indexer.semantic_query(
            query="alpha",
            top_k=2,
            types=[IntelligenceType.TECHINT],
            projects=["alpha"],
        )

    assert [result["id"] for result in results] == ["intel-alpha", "intel-shared"]
    provider.search.assert_called_once_with(
        [0.4, 0.6],
        top_k=3,
        filters={"type": "techint"},
        namespace=None,
        min_score=0.3,
    )


def test_get_stats_reports_provider_backend(tmp_path):
    cerebro = CerebroIntelligence(
        arch_path=str(tmp_path / "arch"),
        data_dir=str(tmp_path / "data"),
    )
    provider = MagicMock(spec=VectorStoreProvider)
    provider.backend_name = "pgvector"
    provider.get_document_count.return_value = 7
    provider.get_backend_info.return_value = {
        "backend": "pgvector",
        "collection_name": "cerebro_documents",
        "schema": "public",
        "table_name": "cerebro_documents",
    }

    with patch("cerebro.registry.indexer.EmbeddingSystem"):
        indexer = KnowledgeIndexer(cerebro, vector_store_provider=provider)

    stats = indexer.get_stats()

    assert stats["backend"] == "pgvector"
    assert stats["indexed_items"] == 7
    assert stats["table_name"] == "cerebro_documents"
