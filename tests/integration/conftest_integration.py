"""
Shared fixtures and utilities for backend integration tests.

All integration tests are gated by CEREBRO_RUN_INTEGRATION=1 environment variable.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import pytest

# Gate all integration tests
INTEGRATION = os.getenv("CEREBRO_RUN_INTEGRATION", "").strip() in ("1", "true", "yes")


@pytest.fixture
def integration_namespace() -> str:
    """
    Unique namespace per test to avoid cross-contamination.
    
    Each test gets its own isolated namespace that can be cleaned up
    independently without affecting other tests.
    """
    return f"inttest-{uuid.uuid4().hex[:12]}"


@pytest.fixture
def sample_documents_fixture(integration_namespace: str) -> list[dict[str, Any]]:
    """Standard test corpus for all backends."""
    return [
        {
            "id": "doc-semantic-1",
            "content": "Cerebro is a distributed RAG platform built on NATS JetStream for scalable document indexing and retrieval.",
            "title": "Cerebro Overview",
            "source": "docs/intro.md",
            "type": "documentation",
            "repo": "cerebro",
            "namespace": integration_namespace,
        },
        {
            "id": "doc-semantic-2", 
            "content": "Vector embeddings enable semantic search by converting text into high-dimensional representations that capture meaning.",
            "title": "Vector Embeddings",
            "source": "docs/embeddings.md",
            "type": "documentation",
            "repo": "cerebro",
            "namespace": integration_namespace,
        },
        {
            "id": "doc-semantic-3",
            "content": "pgvector is a PostgreSQL extension that enables efficient similarity search on dense vectors using HNSW indexes.",
            "title": "pgvector Guide",
            "source": "docs/pgvector.md",
            "type": "tutorial",
            "repo": "cerebro",
            "namespace": integration_namespace,
        },
        {
            "id": "doc-semantic-4",
            "content": "Qdrant is a vector database designed for production-scale similarity search with full query support.",
            "title": "Qdrant Quickstart",
            "source": "guides/qdrant.md",
            "type": "guide",
            "repo": "other-repo",
            "namespace": integration_namespace,
        },
        {
            "id": "doc-semantic-5",
            "content": "OpenSearch extends Elasticsearch with vector search capabilities for hybrid BM25 and dense search.",
            "title": "OpenSearch Vector",
            "source": "docs/opensearch.md", 
            "type": "documentation",
            "repo": "cerebro",
            "namespace": integration_namespace,
        },
    ]


@pytest.fixture
def sample_embeddings_fixture() -> list[list[float]]:
    """
    Standard synthetic embeddings for testing (768 dimensions).
    
    In real scenarios, these would come from an embedding model.
    For testing, we use deterministic synthetic embeddings.
    """
    # Create 5 distinct 768-dimensional embeddings
    embeddings = []
    for i in range(5):
        # Each embedding starts with the doc index, then fills with scaled values
        embedding = [float(i)] + [
            (j + i * 0.1) % 1.0 for j in range(767)
        ]
        embeddings.append(embedding)
    return embeddings


def requires_backend(backend_name: str):
    """
    Decorator to skip tests if the required backend is not active.
    
    Usage:
        @requires_backend("pgvector")
        def test_something(provider):
            ...
    """
    def decorator(test_func):
        active_backend = os.getenv("CEREBRO_VECTOR_STORE_PROVIDER", "").strip()
        should_skip = active_backend != backend_name
        return pytest.mark.skipif(
            should_skip,
            reason=f"Test requires CEREBRO_VECTOR_STORE_PROVIDER={backend_name}, got {active_backend!r}"
        )(test_func)
    return decorator


def skip_if_no_connection(backend_name: str, exception_type: type[Exception]):
    """
    Decorator to skip tests if the backend is not accessible.
    
    Attempts to build a provider and catches connection errors.
    
    Usage:
        @skip_if_no_connection("pgvector", psycopg.OperationalError)
        def test_something():
            ...
    """
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            try:
                from cerebro.providers.vector_store_factory import build_vector_store_provider
                provider = build_vector_store_provider()
                if not provider.health_check():
                    pytest.skip(f"{backend_name} backend not healthy")
            except exception_type as e:
                pytest.skip(f"Cannot connect to {backend_name} backend: {e}")
            return test_func(*args, **kwargs)
        return wrapper
    return decorator
