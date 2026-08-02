# Integration Tests for Backend Providers

This directory contains comprehensive integration test suites for all Cerebro vector store backends.

## Overview

Each backend has its own test module that validates the provider contract:

- `test_pgvector_integration.py` — PostgreSQL + pgvector
- `test_qdrant_integration.py` — Qdrant vector database
- `test_opensearch_integration.py` — OpenSearch / Elasticsearch
- `test_azure_search_integration.py` — Azure AI Search
- `test_weaviate_integration.py` — Weaviate vector store

## Test Coverage

Each backend test suite covers:

1. **Schema Bootstrap** — `initialize_schema()` succeeds
2. **Ingestion** — `upsert_documents()` adds documents with embeddings
3. **Search** — Semantic search returns ranked results
4. **Metadata Filters** — Filters restrict results correctly
5. **Namespace Isolation** — Documents in different namespaces don't leak
6. **Idempotent Re-ingestion** — Re-upserting same docs doesn't duplicate
7. **Deletion** — `delete_documents()` removes by ID
8. **Namespace Clearing** — `clear()` removes all documents from a namespace
9. **Health Checks** — `health_check()` returns healthy status
10. **Backend Info** — Metadata is observable and correct
11. **Export** — Documents can be exported with embeddings (if supported)
12. **Score Filtering** — `min_score` threshold filters results

## Running Tests

### Prerequisites

All integration tests are **gated by the `CEREBRO_RUN_INTEGRATION=1` environment variable**. They automatically skip if not set.

### pgvector Backend

```bash
nix develop .#rag-pgvector --command \
  CEREBRO_RUN_INTEGRATION=1 \
  CEREBRO_VECTOR_STORE_PROVIDER=pgvector \
  pytest tests/integration/test_pgvector_integration.py -v
```

Requires: PostgreSQL running with pgvector extension.

### Qdrant Backend

```bash
nix develop .#rag-qdrant --command \
  CEREBRO_RUN_INTEGRATION=1 \
  CEREBRO_VECTOR_STORE_PROVIDER=qdrant \
  pytest tests/integration/test_qdrant_integration.py -v
```

Requires: Qdrant running at configured URL.

### OpenSearch Backend

```bash
nix develop .#rag-opensearch --command \
  CEREBRO_RUN_INTEGRATION=1 \
  CEREBRO_VECTOR_STORE_PROVIDER=opensearch \
  pytest tests/integration/test_opensearch_integration.py -v
```

Requires: OpenSearch running at configured URL.

### Azure AI Search Backend

```bash
CEREBRO_RUN_INTEGRATION=1 \
CEREBRO_VECTOR_STORE_PROVIDER=azure_search \
pytest tests/integration/test_azure_search_integration.py -v
```

Requires: Azure AI Search credentials in environment.

### Weaviate Backend

```bash
nix develop .#rag-weaviate --command \
  CEREBRO_RUN_INTEGRATION=1 \
  CEREBRO_VECTOR_STORE_PROVIDER=weaviate \
  pytest tests/integration/test_weaviate_integration.py -v
```

Requires: Weaviate running at configured URL.

## Test Structure

All tests follow a consistent pattern:

1. **Provider Fixture** — Instantiates the backend provider and skips if not available
2. **Namespace Isolation** — Each test uses a unique namespace for cleanup
3. **Sample Data** — Standardized test corpus (5 documents, 768-dim embeddings)
4. **Assertions** — Validate contract compliance

### Namespace Isolation

Each test automatically gets a unique namespace (`inttest-<random-12-chars>`) to prevent cross-contamination. Tests can be run in parallel safely.

Example:
```python
def test_example(provider, integration_namespace, sample_documents_fixture):
    provider.upsert_documents(
        sample_documents_fixture,
        ...,
        namespace=integration_namespace,  # Isolated per test
    )
```

### Skipping on Backend Unavailability

Tests gracefully skip if:
- Backend provider can't be instantiated
- Backend is not accessible (health check fails)
- Wrong backend configured (provider.backend_name mismatch)

Example output when backend not running:
```
tests/integration/test_pgvector_integration.py::TestPgvectorIntegration::test_initialize_schema_succeeds SKIPPED [reason: Cannot connect to pgvector backend: ...]
```

## Configuration

Backend configuration comes from environment variables (see `src/cerebro/settings.py`):

- `CEREBRO_VECTOR_STORE_PROVIDER` — Backend name (pgvector, qdrant, opensearch, azure_search, weaviate)
- `CEREBRO_VECTOR_STORE_URL` — Backend connection URL
- `CEREBRO_VECTOR_STORE_NAMESPACE` — Default namespace
- Backend-specific keys (e.g., `CEREBRO_PGVECTOR_DSN`, `CEREBRO_QDRANT_URL`)

## Adding New Backend Tests

To add tests for a new backend:

1. Create `test_<backend>_integration.py` from an existing template
2. Update the backend name check in the provider fixture
3. Add backend-specific skips if needed (e.g., OpenSearch doesn't export embeddings)
4. Add to Nix dev shell if needed
5. Update this README

## Debugging Failed Tests

Common issues:

### "Cannot instantiate provider"
The backend is not configured. Set `CEREBRO_VECTOR_STORE_PROVIDER` and connection env vars.

### "Health check failed"
The backend service is not running. Start it before running tests:
- pgvector: `postgres` must be running with pgvector extension
- Qdrant: `qdrant` service
- OpenSearch: `opensearch` service
- Azure: Requires cloud instance
- Weaviate: `weaviate` service

### Test times out
The backend may be slow or network issues. Increase pytest timeout:
```bash
pytest tests/integration/test_<backend>_integration.py --timeout=60
```

### Score filtering test fails
Some backends may not support `min_score` filtering. Check provider implementation.

## CI Integration

These tests are designed to run in CI/CD pipelines with:

```yaml
matrix:
  backend: [pgvector, qdrant, opensearch, weaviate]
  
steps:
  - name: Run integration tests
    run: |
      nix develop .#rag-${{ matrix.backend }} --command \
        CEREBRO_RUN_INTEGRATION=1 \
        CEREBRO_VECTOR_STORE_PROVIDER=${{ matrix.backend }} \
        pytest tests/integration/test_${{ matrix.backend }}_integration.py -v
```

## See Also

- [Backend Selection Guide](../../docs/guides/runbooks/backend_selection.md)
- [Provider Documentation](../../src/cerebro/providers/)
- [VectorStoreProvider Interface](../../src/cerebro/interfaces/vector_store.py)
