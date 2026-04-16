# Cerebro RAG Production Expansion TODO

**Date:** 2026-04-08
**Scope:** Extend Cerebro from a local-first RAG stack into a production-ready, multi-backend retrieval platform.
**Status:** Planning document for implementation.

---

## 1. Verified Baseline

This TODO is based on the current repository state:

- `src/cerebro/interfaces/vector_store.py` defines the current `VectorStoreProvider` contract.
- `src/cerebro/providers/chroma/` is the only in-tree vector store provider today.
- `src/cerebro/core/rag/engine.py` defaults to local retrieval with Chroma.
- `src/cerebro/registry/indexer.py` maintains a separate FAISS-based semantic index for intelligence search.
- `docs/architecture/ARCHITECTURE.md` already positions the product as local-first and provider-oriented.

What is not yet true in the current codebase:

- no production-grade vector store provider is implemented in-tree besides the local Chroma path
- no unified provider registry/config layer exists for vector backends
- no tenant/namespace/filter contract exists across all retrieval paths
- no production runbook exists for backend selection, migrations, or rollback

---

## 2. Objective

Deliver a production-capable RAG platform with:

- pluggable vector stores
- explicit production and development backend profiles
- metadata filtering and namespace isolation
- deterministic ingestion and re-ingestion semantics
- health checks, observability, and rollback procedures
- Nix-first environment support for each backend track

---

## 3. Backend Strategy

### Development / local baseline

- [ ] Keep `ChromaDB` as the default local backend for one-shot development and small-scale demos.
- [ ] Harden the Chroma adapter so failures do not silently degrade grounded behavior.

### Production backends to add

- [ ] **Priority 1: pgvector**
  - Good fit for production environments that already operate PostgreSQL.
  - Strong transactional behavior and simpler operational footprint than a dedicated vector cluster.
- [ ] **Priority 2: Qdrant**
  - Purpose-built vector database with strong filtering and collection controls.
  - Good candidate for dedicated semantic retrieval workloads.
- [ ] **Priority 3: OpenSearch / Elasticsearch**
  - Useful when hybrid search, existing log/search estate, or enterprise ops tooling already exists.
  - Treat this as a hybrid retrieval backend, not only a vector backend.
- [ ] **Priority 4: Weaviate**
  - Optional enterprise/backend track if the product needs object-centric retrieval or an external managed cluster.
  - Server packaging in `nixpkgs` is not yet verified in this repo context; plan for external cluster/container until verified.

### Existing optional cloud path

- [ ] Keep the current GCP/Vertex path as an optional adapter track.
- [ ] Do not let Vertex-specific behavior define the core vector store interface.

---

## 4. Verified Nix Dependency Mapping

Verified locally via `nix eval` on 2026-04-08:

- Runtime packages:
  - [ ] `postgresql`
  - [ ] `qdrant`
  - [ ] `opensearch`
  - [ ] `elasticsearch`
- Python packages:
  - [ ] `python313Packages.psycopg`
  - [ ] `python313Packages."qdrant-client"`
  - [ ] `python313Packages."weaviate-client"`
  - [ ] `python313Packages."opensearch-py"`
  - [ ] `python313Packages.elasticsearch`
  - [ ] `python313Packages.sqlalchemy`

Open item:

- [ ] Verify whether a first-class `nixpkgs` package for the Weaviate server should be used, or whether the project should standardize on an external deployment model for that backend.

---

## 5. Architecture TODO

### 5.1 Vector store contract v2

- [ ] Extend `VectorStoreProvider` to support production semantics:
  - namespaces / collections
  - upsert semantics
  - metadata filters
  - optional score threshold
  - backend info / health details
  - index bootstrap / migration hooks
- [ ] Add a typed retrieval result model instead of passing raw dictionaries everywhere.
- [ ] Define one canonical metadata schema for all documents:
  - `id`
  - `repo`
  - `source`
  - `title`
  - `chunk_id`
  - `content_hash`
  - `ingested_at`
  - `git_commit`
  - `tags`
  - `backend_namespace`

### 5.2 Provider registry and settings

- [ ] Introduce a central config/settings module for:
  - `CEREBRO_VECTOR_STORE_PROVIDER`
  - `CEREBRO_VECTOR_STORE_URL`
  - `CEREBRO_VECTOR_STORE_NAMESPACE`
  - backend-specific credentials and TLS settings
- [ ] Replace backend selection by implicit defaulting with an explicit provider factory.
- [ ] Ensure the CLI, API, dashboard, and tests all resolve providers through the same factory.

### 5.3 Unify the two semantic paths

- [ ] Decide whether `registry/indexer.py` remains FAISS-only for intelligence search or should also become provider-backed.
- [ ] Eliminate semantic capability drift between:
  - `src/cerebro/core/rag/engine.py`
  - `src/cerebro/registry/indexer.py`
  - `src/cerebro/api/server.py`
- [ ] Standardize filtering semantics so project-scoped and type-scoped queries behave identically in keyword and semantic paths.

---

## 6. Provider Implementation TODO

### 6.1 Chroma hardening

- [ ] Replace `print()`-based error handling with structured logging.
- [ ] Stop treating vector-store failure as “zero documents found”.
- [ ] Add collection bootstrap checks and clearer corruption diagnostics.
- [ ] Add an explicit “development-only” support statement to docs and health output.

### 6.2 pgvector provider

- [ ] Add `src/cerebro/providers/pgvector/`.
- [ ] Implement:
  - connection bootstrap
  - extension verification (`CREATE EXTENSION vector`)
  - table/index creation
  - upsert by `id`
  - metadata filtering
  - delete by id / namespace
  - similarity search with score normalization
- [ ] Support both direct `psycopg` usage and optional SQLAlchemy integration only where it adds value.
- [ ] Add a migration/bootstrap command for local and staging setup.

### 6.3 Qdrant provider

- [ ] Add `src/cerebro/providers/qdrant/`.
- [ ] Implement collection creation, payload mapping, upsert, search, delete, count, and health checks.
- [ ] Map Cerebro metadata into Qdrant payload filters without losing canonical field names.
- [ ] Add support for remote cluster URL + API key configuration.

### 6.4 OpenSearch / Elasticsearch provider

- [ ] Add `src/cerebro/providers/opensearch/`.
- [ ] Decide whether Elasticsearch compatibility stays in the same provider or in a sibling adapter.
- [ ] Implement:
  - index template bootstrap
  - dense vector mapping
  - hybrid retrieval hooks
  - metadata filter translation
  - health and cluster version checks
- [ ] Define which features are guaranteed in OpenSearch and which are version-specific.

### 6.5 Weaviate provider

- [ ] Add `src/cerebro/providers/weaviate/`.
- [ ] Implement collection/class bootstrap, object upsert, hybrid filters, and health checks.
- [ ] Decide whether the provider will require an external embedder only, or optionally delegate embeddings to Weaviate modules.

---

## 7. Retrieval and Ranking TODO

- [ ] Add metadata-aware retrieval filters to `RigorousRAGEngine`.
- [ ] Add namespace-aware retrieval so multiple projects/environments can coexist safely.
- [ ] Add optional hybrid search:
  - dense retrieval
  - sparse/BM25 retrieval
  - reranking
- [ ] Add score normalization per backend so `top_k` behavior remains comparable.
- [ ] Add chunk provenance to citations so output can reference a stable source, not only a free-form title.
- [ ] Refuse to label answers as grounded when retrieval failed or returned no usable context.

---

## 8. Ingestion TODO

- [ ] Make ingestion idempotent.
- [ ] Add content hashing so unchanged chunks are not re-embedded.
- [ ] Add re-index / delete stale chunks behavior for renamed or removed files.
- [ ] Add batch sizing policy per backend.
- [ ] Add backend-specific ingestion metrics:
  - documents accepted
  - documents skipped
  - documents updated
  - failed writes
  - batch latency
- [ ] Add dry-run mode for ingestion planning.

---

## 9. API / CLI / Dashboard TODO

- [ ] Add CLI provider selection and introspection:
  - `cerebro rag backends list`
  - `cerebro rag backend info`
  - `cerebro rag backend health`
- [ ] Add CLI bootstrap helpers:
  - `cerebro rag backend init`
  - `cerebro rag backend migrate`
- [ ] Expose backend name, namespace, document count, and filter support in API health/status endpoints.
- [ ] Surface retrieval backend details in dashboard metrics and health panels.
- [ ] Make project-scoped chat requests actually respect project scope in semantic retrieval.

---

## 10. Observability and Operations TODO

- [ ] Emit structured logs for ingestion, retrieval, rerank, and provider health.
- [ ] Add backend-specific readiness and liveness checks.
- [ ] Add latency histograms and failure counters per provider.
- [ ] Add index size / collection size reporting.
- [ ] Add migration and rollback runbooks for each production backend.
- [ ] Add backup/restore guidance:
  - PostgreSQL logical backup / restore
  - Qdrant snapshot policy
  - OpenSearch snapshot repository policy
  - Weaviate backup/export policy

---

## 11. Security TODO

- [ ] Require TLS/auth config for remote production backends.
- [ ] Ensure secrets are passed via environment or secret files, never committed config.
- [ ] Add namespace isolation guidance for multi-tenant or multi-project deployments.
- [ ] Review metadata fields to avoid leaking sensitive path or credential material into indexes.
- [ ] Add audit guidance for delete requests and retention windows.

---

## 12. Nix / Flake TODO

- [ ] Remove hidden dependency installation from `shellHook` where possible.
- [ ] Add explicit dev shells or packages for backend tracks:
  - [ ] `.#rag-pgvector`
  - [ ] `.#rag-qdrant`
  - [ ] `.#rag-opensearch`
- [ ] Keep the default shell lightweight and local-first.
- [ ] Ensure each optional backend shell declares only the dependencies it needs.
- [ ] Add one-shot commands that follow project policy:
  - `nix develop --command ...`
  - `nix develop .#rag-pgvector --command ...`
  - `nix develop .#rag-qdrant --command ...`

---

## 13. Testing TODO

### Unit tests

- [ ] Add provider contract tests shared by all vector backends.
- [ ] Add serialization/filter mapping tests for canonical metadata.
- [ ] Add engine tests for:
  - empty context
  - backend failure
  - namespace mismatch
  - filter mismatch
  - duplicate document upsert

### Integration tests

- [ ] Add integration suites per backend.
- [ ] Gate optional suites behind backend-specific Nix shells and env flags.
- [ ] Cover:
  - bootstrap
  - ingest
  - query
  - filtered query
  - re-ingest
  - delete
  - health check

### Performance tests

- [ ] Benchmark ingestion throughput by backend.
- [ ] Benchmark query latency p50/p95 by backend.
- [ ] Benchmark recall quality with the same corpus and query set.
- [ ] Define a regression budget so backend additions do not silently degrade local mode.

---

## 14. Rollout Plan

### Phase 0: Contract hardening

- [ ] finalize `VectorStoreProvider` v2
- [ ] add provider factory/settings
- [ ] fix grounded/no-context behavior
- [ ] align semantic filter behavior

### Phase 1: First production backend

- [ ] implement `pgvector`
- [ ] ship tests, Nix shell, bootstrap command, docs
- [ ] validate ingestion/query flow end-to-end

### Phase 2: Dedicated vector DB backend

- [ ] implement `Qdrant`
- [ ] compare operational and retrieval trade-offs vs. pgvector

### Phase 3: Hybrid search backend

- [ ] implement `OpenSearch / Elasticsearch`
- [ ] add hybrid retrieval mode and filtering tests

### Phase 4: Optional enterprise backend

- [ ] implement `Weaviate`
- [ ] validate whether it remains worth maintaining in-tree

### Phase 5: Production polish

- [ ] observability
- [ ] runbooks
- [ ] migration stories
- [ ] rollback stories
- [ ] dashboard exposure

---

## 15. Definition of Done

A backend is only considered production-ready when all of the following are true:

- [ ] provider is selected through the shared factory/config path
- [ ] ingestion is idempotent
- [ ] metadata filters work
- [ ] namespaces work
- [ ] health checks return actionable detail
- [ ] integration tests pass in `nix develop --command` or a backend-specific shell
- [ ] benchmark data exists
- [ ] operational runbook exists
- [ ] rollback procedure exists
- [ ] docs clearly state when the backend should and should not be chosen

---

## 16. Recommended Order of Execution

1. Fix the provider contract and retrieval semantics first.
2. Implement `pgvector` as the first production backend.
3. Implement `Qdrant` as the dedicated vector DB option.
4. Add OpenSearch only when hybrid search is a real product requirement.
5. Keep Weaviate optional until there is a concrete adoption need.
