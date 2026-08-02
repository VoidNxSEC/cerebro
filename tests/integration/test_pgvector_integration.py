"""
Integration test suite for pgvector backend.

Gated by CEREBRO_RUN_INTEGRATION=1 (skip if not set).
Requires: PostgreSQL with pgvector extension running at connection URL in settings.

Run with:
    nix develop .#rag-pgvector --command \\
        CEREBRO_RUN_INTEGRATION=1 \\
        CEREBRO_VECTOR_STORE_PROVIDER=pgvector \\
        pytest tests/integration/test_pgvector_integration.py -v

Each test runs in isolation using unique namespaces to prevent cross-contamination.
"""

from __future__ import annotations

import os
import pytest

INTEGRATION = os.getenv("CEREBRO_RUN_INTEGRATION", "").strip() in ("1", "true", "yes")
pytestmark = pytest.mark.skipif(not INTEGRATION, reason="set CEREBRO_RUN_INTEGRATION=1 to run")


@pytest.fixture(scope="function")
def provider():
    """
    Instantiate and return the active vector store provider.
    
    Skips the test if the backend is not available.
    """
    try:
        from cerebro.providers.vector_store_factory import build_vector_store_provider
        provider = build_vector_store_provider()
        
        # Verify it's actually pgvector
        if provider.backend_name != "pgvector":
            pytest.skip(
                f"Expected pgvector backend, got {provider.backend_name}. "
                "Set CEREBRO_VECTOR_STORE_PROVIDER=pgvector"
            )
        
        # Check health
        if not provider.health_check():
            pytest.skip("pgvector backend not healthy")
        
        return provider
    except Exception as e:
        pytest.skip(f"Cannot instantiate pgvector provider: {e}")


# ============================================================================
# Test Suite: pgvector Backend Contract
# ============================================================================


class TestPgvectorIntegration:
    """Integration tests for pgvector backend conformance."""

    def test_initialize_schema_succeeds(self, provider):
        """Schema bootstrap creates table and indexes."""
        result = provider.initialize_schema()
        
        assert result["backend"] == "pgvector"
        assert result["initialized"] is True
        assert "table_name" in result

    def test_upsert_documents_ingests_batch(
        self,
        provider,
        integration_namespace,
        sample_documents_fixture,
        sample_embeddings_fixture,
    ):
        """Upsert a batch of documents into the store."""
        # Use only first 3 docs for this test
        docs = sample_documents_fixture[:3]
        embeddings = sample_embeddings_fixture[:3]
        
        count = provider.upsert_documents(
            docs,
            embeddings,
            namespace=integration_namespace,
        )
        
        assert count == 3, f"Expected 3 documents inserted, got {count}"
        
        # Verify count
        stored_count = provider.get_document_count(namespace=integration_namespace)
        assert stored_count >= 3

    def test_search_returns_ranked_results(
        self,
        provider,
        integration_namespace,
        sample_documents_fixture,
        sample_embeddings_fixture,
    ):
        """Semantic search returns results ranked by similarity."""
        # Ingest documents
        docs = sample_documents_fixture[:3]
        embeddings = sample_embeddings_fixture[:3]
        provider.upsert_documents(
            docs,
            embeddings,
            namespace=integration_namespace,
        )
        
        # Search using first embedding
        query_embedding = sample_embeddings_fixture[0]
        results = provider.search(
            query_embedding,
            top_k=5,
            namespace=integration_namespace,
        )
        
        assert len(results) > 0, "Expected at least one search result"
        
        # Check structure
        for result in results:
            assert result.id is not None
            assert 0.0 <= result.score <= 1.0, f"Score out of range: {result.score}"
            assert result.namespace == integration_namespace
            
        # Results should be sorted by score (highest first)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_with_metadata_filters(
        self,
        provider,
        integration_namespace,
        sample_documents_fixture,
        sample_embeddings_fixture,
    ):
        """Metadata filters restrict search results correctly."""
        # Ingest all documents
        docs = sample_documents_fixture
        embeddings = sample_embeddings_fixture
        provider.upsert_documents(
            docs,
            embeddings,
            namespace=integration_namespace,
        )
        
        # Search with repo filter
        query_embedding = sample_embeddings_fixture[0]
        results = provider.search(
            query_embedding,
            top_k=10,
            filters={"repo": "cerebro"},
            namespace=integration_namespace,
        )
        
        # All results should have repo="cerebro"
        for result in results:
            assert result.metadata.get("repo") == "cerebro"

    def test_namespace_isolation(
        self,
        provider,
        sample_documents_fixture,
        sample_embeddings_fixture,
    ):
        """Documents in different namespaces don't leak between searches."""
        ns1 = "inttest-ns1-" + "a" * 8
        ns2 = "inttest-ns2-" * 4
        
        docs1 = sample_documents_fixture[:2]
        embeddings1 = sample_embeddings_fixture[:2]
        
        docs2 = sample_documents_fixture[2:4]
        embeddings2 = sample_embeddings_fixture[2:4]
        
        # Ingest into different namespaces
        count1 = provider.upsert_documents(docs1, embeddings1, namespace=ns1)
        count2 = provider.upsert_documents(docs2, embeddings2, namespace=ns2)
        
        assert count1 == 2
        assert count2 == 2
        
        # Query in ns1
        results_ns1 = provider.search(
            sample_embeddings_fixture[0],
            top_k=10,
            namespace=ns1,
        )
        
        # All results should be in ns1
        assert all(r.namespace == ns1 for r in results_ns1)
        
        # Query in ns2
        results_ns2 = provider.search(
            sample_embeddings_fixture[2],
            top_k=10,
            namespace=ns2,
        )
        
        # All results should be in ns2
        assert all(r.namespace == ns2 for r in results_ns2)

    def test_idempotent_reingest(
        self,
        provider,
        integration_namespace,
        sample_documents_fixture,
        sample_embeddings_fixture,
    ):
        """Re-upserting the same documents does not duplicate entries."""
        docs = sample_documents_fixture[:2]
        embeddings = sample_embeddings_fixture[:2]
        
        # First ingest
        count1 = provider.upsert_documents(
            docs,
            embeddings,
            namespace=integration_namespace,
        )
        total_after_first = provider.get_document_count(namespace=integration_namespace)
        
        # Re-ingest same documents
        count2 = provider.upsert_documents(
            docs,
            embeddings,
            namespace=integration_namespace,
        )
        total_after_second = provider.get_document_count(namespace=integration_namespace)
        
        # Count should not increase on re-ingest
        assert total_after_first == total_after_second, (
            f"Count increased after re-ingest: {total_after_first} → {total_after_second}"
        )

    def test_delete_documents_by_id(
        self,
        provider,
        integration_namespace,
        sample_documents_fixture,
        sample_embeddings_fixture,
    ):
        """Delete removes documents by ID."""
        docs = sample_documents_fixture[:3]
        embeddings = sample_embeddings_fixture[:3]
        
        # Ingest
        provider.upsert_documents(
            docs,
            embeddings,
            namespace=integration_namespace,
        )
        count_before = provider.get_document_count(namespace=integration_namespace)
        
        # Delete first document
        delete_ids = [docs[0]["id"]]
        deleted = provider.delete_documents(delete_ids, namespace=integration_namespace)
        
        assert deleted == 1
        
        count_after = provider.get_document_count(namespace=integration_namespace)
        assert count_after == count_before - 1

    def test_clear_namespace(
        self,
        provider,
        integration_namespace,
        sample_documents_fixture,
        sample_embeddings_fixture,
    ):
        """Clear removes all documents from a namespace."""
        docs = sample_documents_fixture[:3]
        embeddings = sample_embeddings_fixture[:3]
        
        # Ingest
        provider.upsert_documents(
            docs,
            embeddings,
            namespace=integration_namespace,
        )
        assert provider.get_document_count(namespace=integration_namespace) > 0
        
        # Clear namespace
        provider.clear(namespace=integration_namespace)
        
        count_after = provider.get_document_count(namespace=integration_namespace)
        assert count_after == 0

    def test_health_check_returns_true(self, provider):
        """Health check passes when backend is accessible."""
        is_healthy = provider.health_check()
        assert is_healthy is True

    def test_get_backend_info_returns_metadata(self, provider):
        """Backend info provides observable metadata."""
        info = provider.get_backend_info()
        
        assert "backend" in info
        assert info["backend"] == "pgvector"

    def test_export_documents_with_embeddings(
        self,
        provider,
        integration_namespace,
        sample_documents_fixture,
        sample_embeddings_fixture,
    ):
        """Export returns documents with embeddings for migration."""
        docs = sample_documents_fixture[:2]
        embeddings = sample_embeddings_fixture[:2]
        
        # Ingest
        provider.upsert_documents(
            docs,
            embeddings,
            namespace=integration_namespace,
        )
        
        # Export
        exported = provider.export_documents(namespace=integration_namespace)
        
        assert len(exported) > 0
        
        for doc in exported:
            assert doc.id is not None
            assert doc.content is not None
            assert doc.embedding is not None
            assert len(doc.embedding) > 0

    def test_min_score_threshold(
        self,
        provider,
        integration_namespace,
        sample_documents_fixture,
        sample_embeddings_fixture,
    ):
        """min_score parameter filters results by score threshold."""
        docs = sample_documents_fixture[:5]
        embeddings = sample_embeddings_fixture[:5]
        
        # Ingest
        provider.upsert_documents(
            docs,
            embeddings,
            namespace=integration_namespace,
        )
        
        # Search with high min_score
        query_embedding = sample_embeddings_fixture[0]
        results_filtered = provider.search(
            query_embedding,
            top_k=10,
            min_score=0.9,
            namespace=integration_namespace,
        )
        
        # All results should meet the threshold
        for result in results_filtered:
            assert result.score >= 0.9


class TestPgvectorCleanup:
    """Cleanup tests ensure isolation between test runs."""

    def test_cleanup_namespace_isolation(
        self,
        provider,
        sample_documents_fixture,
        sample_embeddings_fixture,
    ):
        """Each test namespace is independently cleanable."""
        ns = "inttest-cleanup-" + "x" * 8
        
        docs = sample_documents_fixture[:1]
        embeddings = sample_embeddings_fixture[:1]
        
        provider.upsert_documents(docs, embeddings, namespace=ns)
        assert provider.get_document_count(namespace=ns) > 0
        
        provider.clear(namespace=ns)
        assert provider.get_document_count(namespace=ns) == 0
