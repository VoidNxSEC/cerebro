# RAG Pipeline Operational Runbook

**Scope:** End-to-end ingestion, query, and reranking operations for Cerebro's RAG pipeline.  
**Key paths:** `src/cerebro/core/rag/`, `src/cerebro/registry/indexer.py`, `src/cerebro/core/rerank_client.py`

---

## Architecture Overview

```
Source (git repo / files)
        │
        ▼
  KnowledgeIndexer             ← registry/indexer.py
  build_canonical_fields()     ← core/metadata.py (content_hash, chunk_id, ingested_at)
        │
        ▼
  VectorStoreProvider.upsert_documents()   ← providers/*/
        │
        ▼
  [Vector Store: chroma / pgvector / qdrant / opensearch / weaviate / azure_search]
        │
        ▼  (query time)
  RigorousRAGEngine.query()    ← core/rag/engine.py
  VectorStoreProvider.search()
        │
        ▼
  CerebroRerankerClient.rerank()   ← core/rerank_client.py
  → cerebro-reranker service (POST /v1/rerank)
  → local CrossEncoderReranker fallback
        │
        ▼
  Answer returned to CLI / Dashboard
```

---

## 1. Environment Setup

Minimum required variables:

```bash
# Backend
export CEREBRO_VECTOR_STORE_PROVIDER=chroma        # or pgvector, qdrant, etc.
export CEREBRO_VECTOR_STORE_COLLECTION_NAME=cerebro_documents

# LLM
export CEREBRO_LLM_PROVIDER=llamacpp               # or anthropic, gemini, etc.

# Reranker (optional — falls back to local model)
export CEREBRO_RERANKER_URL=http://localhost:8090
export CEREBRO_RERANKER_MODE=service               # service | local | hybrid
```

---

## 2. Ingestion

### Index a single repository

```bash
nix develop --command cerebro knowledge index-repo \
  --repo-path ./my-service \
  --repo-name my-service

# With namespace isolation
nix develop --command cerebro knowledge index-repo \
  --repo-path ./my-service \
  --repo-name my-service \
  --namespace team-alpha
```

### Index multiple repositories (batch)

```bash
nix develop --command cerebro knowledge batch-analyze \
  --config repos.yaml
```

`repos.yaml` format:
```yaml
repos:
  - path: ./service-a
    name: service-a
    namespace: team-alpha
  - path: ./service-b
    name: service-b
    namespace: team-beta
```

### Ingest via RAG subcommand

```bash
nix develop --command cerebro rag ingest \
  --provider chroma \
  --source-dir ./data/docs \
  --namespace project-x
```

### Canonical metadata guaranteed on every ingestion

Every chunk written to the vector store includes:

| Field | Description |
|-------|-------------|
| `content_hash` | SHA-256 of the chunk text — used for dedup |
| `ingested_at` | ISO-8601 UTC timestamp |
| `chunk_id` | `<repo>:<source>:<index>` stable identifier |
| `backend_namespace` | Active namespace at ingestion time |
| `_cerebro_schema_version` | Schema version (`"1"`) |

---

## 3. Query

### CLI query

```bash
nix develop --command cerebro rag query "how does authentication work?"

# Namespace-scoped
nix develop --command cerebro rag query "how does auth work?" \
  --namespace team-alpha

# With filter
nix develop --command cerebro rag query "how does auth work?" \
  --filter type=techint
```

### Smoke test (end-to-end validation)

```bash
nix develop --command cerebro rag smoke
# Ingests a test document, queries it, verifies recall — exits 0 on success
```

### RAG status

```bash
nix develop --command cerebro rag status
# Shows: provider, collection, document count, hybrid support, schema version
```

---

## 4. Backend Management

```bash
# List all registered backends and capabilities
nix develop --command cerebro rag backends list

# Show active backend info
nix develop --command cerebro rag backend info

# Health check active backend
nix develop --command cerebro rag backend health

# Bootstrap schema (idempotent — safe to run repeatedly)
nix develop --command cerebro rag backend init

# Run smoke test against active backend
nix develop --command cerebro rag backend smoke
```

---

## 5. Reranking

The reranker runs as a sidecar (`cerebro-reranker`, port 8090). The RAG engine
calls it automatically post-retrieval. No manual intervention needed in normal operation.

```bash
# Check reranker health
curl http://localhost:8090/health

# Manual rerank call
curl -sX POST http://localhost:8090/v1/rerank \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "how does auth work?",
    "documents": ["doc text 1", "doc text 2"],
    "top_k": 5
  }' | jq .
```

If the reranker service is unreachable, `CerebroRerankerClient` automatically
falls back to the local `CrossEncoderReranker` (MiniLM). No action required.

Force local mode:
```bash
export CEREBRO_RERANKER_MODE=local
```

---

## 6. Namespace Isolation

Namespaces allow multi-tenant or multi-project data partitioning within a single
collection/index:

```bash
# Ingest to namespace
export CEREBRO_VECTOR_STORE_NAMESPACE=project-x
cerebro rag backend init
cerebro knowledge index-repo --repo-path ./src --repo-name api

# Query scoped to namespace
cerebro rag query "describe the API" --namespace project-x

# List documents in namespace (programmatic)
python3 -c "
from cerebro.providers.vector_store_factory import build_vector_store_provider
p = build_vector_store_provider()
print(p.count_documents(namespace='project-x'))
"

# Clear a namespace (non-destructive to other namespaces)
python3 -c "
from cerebro.providers.vector_store_factory import build_vector_store_provider
p = build_vector_store_provider()
p.clear_namespace('project-x')
"
```

---

## 7. Backend Migration

Migrate documents from one backend to another:

```bash
# Migrate Chroma → pgvector (in-tree command)
nix develop --command cerebro rag migrate \
  --from-provider chroma \
  --to-provider pgvector \
  --batch-size 200

# Or use the backend-scoped migrate
nix develop --command cerebro rag backend migrate \
  --from-provider chroma \
  --from-persist-directory ./data/vector_db \
  --batch-size 100
```

Migration reads from the source via `export_documents()` and writes to the
target via `upsert_documents()`. The process is idempotent — re-running
migrates only changed content (content_hash dedup, when implemented).

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `VectorStoreProvider not found` | Wrong `CEREBRO_VECTOR_STORE_PROVIDER` | Check alias list: `cerebro rag backends list` |
| Empty results on query | No data ingested or wrong namespace | Run `cerebro rag backend health`; check namespace |
| Reranker timeout | cerebro-reranker not running | Service falls back to local automatically; start service to improve latency |
| `content_hash` mismatch on upsert | Chunk text changed | Expected — idempotent upsert updates the row |
| High memory on ingestion | Large batch + local embeddings | Reduce batch size; use remote embedding provider |
| `schema_version` mismatch | Old documents in store | Re-ingest; or manually backfill `_cerebro_schema_version` field |

---

## 9. Observability

Key log lines to monitor (structured JSON when in production):

```
INFO  cerebro.core.rag.engine - RAG query completed in 0.42s (retrieved=10, reranked=5)
INFO  cerebro.registry.indexer - Indexed 847 chunks from repo=my-service namespace=team-alpha
WARN  cerebro.core.rerank_client - Reranker service unavailable. Falling back to local model.
ERROR cerebro.providers.pgvector - Failed to upsert 3 documents: connection timeout
```

Performance targets (aspirational):

| Operation | Target |
|-----------|--------|
| Single chunk ingestion | < 50 ms |
| Batch ingestion (100 chunks) | < 5 s |
| RAG query (retrieve + rerank) | < 2 s |
| Backend health check | < 500 ms |
