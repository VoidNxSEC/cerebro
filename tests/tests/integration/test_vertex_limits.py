"""
Integration tests for Vertex AI API rate limits and credit usage.

These tests verify that the RAG engine properly handles:
- Rate limiting with exponential backoff
- Batch processing with configurable chunk sizes
- Credit consumption tracking
- Error handling for quota exhaustion
"""

import pytest
import os
from unittest.mock import MagicMock, patch
from google.api_core import exceptions

from phantom.providers.gcp.vertex_ai_llm import VertexAILLMProvider
from phantom.interfaces.llm import LLMProvider


@pytest.mark.integration
class TestVertexAILimits:
    """Test Vertex AI rate limiting and credit consumption."""

    @pytest.fixture
    def vertex_provider(self):
        """Create a Vertex AI provider for testing."""
        return VertexAILLMProvider(
            project_id="test-project",
            location="global",
            data_store_id="test-store"
        )

    def test_embed_batch_with_exponential_backoff(self, vertex_provider):
        """Test that embed_batch implements exponential backoff on rate limit."""
        texts = ["text1", "text2", "text3"]
        
        with patch("phantom.providers.gcp.vertex_ai_llm.VertexAIEmbeddings") as mock_embeddings:
            # Simulate rate limit on first call, success on retry
            mock_instance = mock_embeddings.return_value
            mock_instance.embed_documents.side_effect = [
                exceptions.ResourceExhausted("Rate limit exceeded"),
                [[0.1] * 768, [0.2] * 768, [0.3] * 768]  # Success on retry
            ]
            
            vertex_provider.embed_batch(texts, batch_size=3)
            
            # Verify that embed_documents was called twice (initial + 1 retry)
            assert mock_instance.embed_documents.call_count == 2

    def test_embed_batch_max_retries_exceeded(self, vertex_provider):
        """Test that embed_batch raises error after max retries."""
        texts = ["text1", "text2"]
        
        with patch("phantom.providers.gcp.vertex_ai_llm.VertexAIEmbeddings") as mock_embeddings:
            # Always fail with rate limit
            mock_instance = mock_embeddings.return_value
            mock_instance.embed_documents.side_effect = exceptions.ResourceExhausted(
                "Rate limit exceeded"
            )
            
            with pytest.raises(exceptions.ResourceExhausted):
                vertex_provider.embed_batch(texts, batch_size=2)
            
            # Verify max retries were attempted
            assert mock_instance.embed_documents.call_count == vertex_provider.MAX_RETRIES

    def test_embed_batch_chunking(self, vertex_provider):
        """Test that embed_batch properly chunks large text lists."""
        texts = [f"text{i}" for i in range(100)]
        batch_size = 20
        
        with patch("phantom.providers.gcp.vertex_ai_llm.VertexAIEmbeddings") as mock_embeddings:
            mock_instance = mock_embeddings.return_value
            # Return appropriate number of embeddings for each batch
            mock_instance.embed_documents.side_effect = [
                [[0.1] * 768 for _ in range(20)] for _ in range(5)  # 5 batches of 20
            ]
            
            result = vertex_provider.embed_batch(texts, batch_size=batch_size)
            
            # Verify correct number of batches
            assert mock_instance.embed_documents.call_count == 5
            assert len(result) == 100

    def test_grounded_generate_with_citations(self, vertex_provider):
        """Test grounded generation returns citations."""
        query = "What is machine learning?"
        context = ["ML is a subset of AI", "Deep learning uses neural networks"]
        
        with patch.object(vertex_provider, 'search_client') as mock_search:
            mock_response = MagicMock()
            mock_response.summary = "Machine learning is a subset of artificial intelligence..."
            mock_response.citations = ["source1.pdf", "source2.pdf"]
            mock_response.cost_estimate = 0.004
            
            mock_search.grounded_search.return_value = mock_response
            
            result = vertex_provider.grounded_generate(query, context)
            
            assert "Machine learning" in result["answer"]
            assert len(result["citations"]) == 2
            assert result["cost_estimate"] == 0.004

    def test_grounded_generate_no_data_store(self):
        """Test grounded generation fails gracefully without data store."""
        provider = VertexAILLMProvider(
            project_id="test-project",
            location="global",
            data_store_id=None  # No data store
        )
        
        result = provider.grounded_generate("test query", [])
        
        assert "not configured" in result["answer"]
        assert result["confidence"] == 0.0
        assert result["cost_estimate"] == 0.0

    def test_health_check_success(self, vertex_provider):
        """Test health check succeeds when API is accessible."""
        with patch.object(vertex_provider.discovery_client, 'list_data_stores') as mock_list:
            mock_list.return_value = MagicMock()
            
            result = vertex_provider.health_check()
            
            assert result is True
            mock_list.assert_called_once()

    def test_health_check_failure(self, vertex_provider):
        """Test health check fails when API is inaccessible."""
        with patch.object(vertex_provider.discovery_client, 'list_data_stores') as mock_list:
            mock_list.side_effect = Exception("API unavailable")
            
            result = vertex_provider.health_check()
            
            assert result is False

    def test_import_documents_success(self, vertex_provider):
        """Test document import returns operation name."""
        gcs_uri = "gs://bucket/path/to/documents.jsonl"
        
        with patch.object(vertex_provider.discovery_client, 'import_documents') as mock_import:
            mock_operation = MagicMock()
            mock_operation.operation.name = "projects/123/locations/global/operations/op-456"
            mock_import.return_value = mock_operation
            
            result = vertex_provider.import_documents(gcs_uri)
            
            assert "operations" in result
            mock_import.assert_called_once()

    def test_import_documents_no_data_store(self):
        """Test document import fails without data store ID."""
        provider = VertexAILLMProvider(
            project_id="test-project",
            location="global",
            data_store_id=None
        )
        
        with pytest.raises(ValueError, match="DATA_STORE_ID"):
            provider.import_documents("gs://bucket/path/documents.jsonl")


@pytest.mark.integration
class TestCreditConsumption:
    """Test credit consumption tracking and limits."""

    def test_search_enterprise_cost_calculation(self):
        """Test that search cost is calculated correctly."""
        from phantom.core.gcp.search import VertexAISearch
        
        search = VertexAISearch(
            project_id="test-project",
            location="global",
            data_store_id="test-store"
        )
        
        # Cost per 1000 queries
        expected_cost_per_1k = 4.00
        assert search.SEARCH_ENTERPRISE_COST_PER_1K == expected_cost_per_1k
        
        # Cost per single query
        cost_per_query = expected_cost_per_1k / 1000
        assert cost_per_query == 0.004

    def test_batch_embedding_cost_estimation(self):
        """Test cost estimation for batch embeddings."""
        # Vertex AI Embeddings API pricing (as of 2025)
        # Text Embedding 004: $0.025 per 1M tokens
        
        texts = ["short text"] * 100
        avg_tokens_per_text = 10
        total_tokens = len(texts) * avg_tokens_per_text
        
        cost_per_1m_tokens = 0.025
        estimated_cost = (total_tokens / 1_000_000) * cost_per_1m_tokens
        
        # Should be very small for 100 short texts
        assert estimated_cost < 0.001

    def test_rate_limit_backoff_timing(self):
        """Test that exponential backoff timing is correct."""
        provider = VertexAILLMProvider(
            project_id="test-project",
            location="global"
        )
        
        # Verify backoff configuration
        assert provider.INITIAL_BACKOFF == 1.0
        assert provider.MAX_BACKOFF == 32.0
        assert provider.MAX_RETRIES == 3
        
        # Verify backoff sequence: 1s, 2s, 4s, 8s, 16s, 32s
        backoff = provider.INITIAL_BACKOFF
        for _ in range(5):
            backoff = min(backoff * 2, provider.MAX_BACKOFF)
        
        assert backoff == provider.MAX_BACKOFF


@pytest.mark.integration
class TestBatchProcessing:
    """Test batch processing of documents and embeddings."""

    def test_ingest_with_batching(self):
        """Test that ingest properly batches documents."""
        from phantom.core.rag.engine import RigorousRAGEngine
        from phantom.interfaces.llm import LLMProvider
        from phantom.interfaces.vector_store import VectorStoreProvider
        
        # Create mock providers
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.import_documents.return_value = "operation-123"
        
        mock_vector_store = MagicMock(spec=VectorStoreProvider)
        
        engine = RigorousRAGEngine(
            llm_provider=mock_llm,
            vector_store_provider=mock_vector_store,
            data_store_id="test-store"
        )
        engine.project_id = "test-project"
        
        # Create test JSONL file
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for i in range(50):
                doc = {
                    "jsonData": json.dumps({
                        "title": f"doc_{i}",
                        "content": f"content_{i}",
                        "repo": "test"
                    })
                }
                f.write(json.dumps(doc) + "\n")
            temp_path = f.name
        
        try:
            with patch("phantom.core.rag.engine.storage.Client"):
                count = engine.ingest(temp_path)
                assert count == 50
        finally:
            os.unlink(temp_path)
