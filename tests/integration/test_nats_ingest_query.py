"""
Integration test: NATS JetStream ingest → vector store query.

Gated by CEREBRO_RUN_INTEGRATION=1 (skip otherwise).
Requires: NATS server running at NATS_URL (default nats://localhost:4222).
Requires: CEREBRO_VECTOR_STORE_PROVIDER set to a live backend.

Run:
    nix develop .#rag-pgvector --command \\
        CEREBRO_RUN_INTEGRATION=1 \\
        CEREBRO_VECTOR_STORE_PROVIDER=pgvector \\
        pytest tests/integration/test_nats_ingest_query.py -v
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid

import pytest

INTEGRATION = os.getenv("CEREBRO_RUN_INTEGRATION", "").strip() in ("1", "true", "yes")

pytestmark = pytest.mark.skipif(not INTEGRATION, reason="set CEREBRO_RUN_INTEGRATION=1 to run")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def namespace() -> str:
    """Unique namespace per test run to avoid cross-contamination."""
    return f"inttest-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def sample_documents(namespace: str) -> list[dict]:
    return [
        {
            "id": f"doc-{i}",
            "content": f"Sample document {i}: cerebro distributed RAG platform on NATS JetStream",
            "namespace": namespace,
            "chunk_index": i,
        }
        for i in range(3)
    ]


@pytest.fixture(scope="module")
def sample_embeddings() -> list[list[float]]:
    # Tiny synthetic embeddings — real tests should use actual embeddings.
    # Dimension must match the backend's configured vector size.
    dim = int(os.getenv("CEREBRO_VECTOR_DIM", "4"))
    return [[float(i + j * 0.1) for j in range(dim)] for i in range(3)]


# ---------------------------------------------------------------------------
# Worker fixture — runs in background for the duration of the module
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def worker_task(event_loop):
    """Start an IngestWorker in the background; stop after tests complete."""
    from cerebro.nats import IngestWorker

    worker = IngestWorker(worker_id="inttest-worker")

    async def _run():
        try:
            await worker.run()
        except Exception:
            pass  # expected on teardown

    task = event_loop.create_task(_run())
    # Give the worker a moment to connect and bind the consumer.
    event_loop.run_until_complete(asyncio.sleep(1.5))
    yield worker
    worker.request_stop()
    event_loop.run_until_complete(asyncio.sleep(0.5))
    task.cancel()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_publish_and_complete(sample_documents, sample_embeddings, namespace, worker_task):
    """Publish an ingest request; assert the worker returns a success completion."""
    from cerebro.nats import IngestRequest, publish_ingest_request

    request = IngestRequest(
        documents=sample_documents,
        embeddings=sample_embeddings,
        namespace=namespace,
    )

    completion = await publish_ingest_request(request, timeout=30.0)

    assert completion.status == "success", f"Expected success, got: {completion.error}"
    assert completion.inserted == len(sample_documents)
    assert completion.correlation_id == request.correlation_id


@pytest.mark.asyncio
async def test_query_after_ingest(sample_documents, sample_embeddings, namespace, worker_task):
    """Query the vector store after ingest; assert at least one result is returned."""
    from cerebro.providers.vector_store_factory import build_vector_store_provider

    provider = build_vector_store_provider()
    query_embedding = sample_embeddings[0]

    results = provider.search(query_embedding, namespace=namespace, top_k=5)

    assert len(results) > 0, "Expected at least one result after ingest"
    assert all(r.namespace == namespace for r in results), "Namespace isolation violated"


@pytest.mark.asyncio
async def test_idempotent_reingest(sample_documents, sample_embeddings, namespace, worker_task):
    """Re-publishing the same documents must not duplicate entries."""
    from cerebro.nats import IngestRequest, publish_ingest_request
    from cerebro.providers.vector_store_factory import build_vector_store_provider

    provider = build_vector_store_provider()
    count_before = provider.document_count(namespace=namespace)

    request = IngestRequest(
        documents=sample_documents,
        embeddings=sample_embeddings,
        namespace=namespace,
    )
    completion = await publish_ingest_request(request, timeout=30.0)
    assert completion.status == "success"

    count_after = provider.document_count(namespace=namespace)
    assert count_after == count_before, (
        f"Re-ingest changed count {count_before} → {count_after}; upsert semantics violated"
    )


@pytest.mark.asyncio
async def test_wrong_embeddings_length_returns_error(sample_documents, namespace, worker_task):
    """A mismatched embeddings list must produce an error completion, not a crash."""
    from cerebro.nats import IngestRequest, publish_ingest_request

    bad_embeddings = [[0.1, 0.2]]  # only 1 embedding for 3 documents
    request = IngestRequest(
        documents=sample_documents,
        embeddings=bad_embeddings,
        namespace=namespace,
    )

    completion = await publish_ingest_request(request, timeout=15.0)

    assert completion.status == "error"
    assert "length" in (completion.error or "").lower()


@pytest.mark.asyncio
async def test_namespace_cleanup(namespace, worker_task):
    """Clearing the namespace must reduce document count to zero."""
    from cerebro.providers.vector_store_factory import build_vector_store_provider

    provider = build_vector_store_provider()
    provider.clear_namespace(namespace=namespace)
    count = provider.document_count(namespace=namespace)
    assert count == 0, f"Expected 0 after clear, got {count}"
