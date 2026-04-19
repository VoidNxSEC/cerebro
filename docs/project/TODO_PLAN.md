# Cerebro RAG Production Expansion TODO

**Last updated:** 2026-04-19
**Scope:** Extend Cerebro from a local-first RAG stack into a production-ready, multi-backend retrieval platform.

---

## Changelog

| Version | Date | Summary |
|---------|------|---------|
| v0.1 | 2026-04-08 | Initial planning document |
| v0.2 | 2026-04-19 | Audit pass — mark completed work; align with actual codebase state |

---

## 1. Verified Baseline

**State at v0.1 (2026-04-08) — original baseline:**

- `src/cerebro/providers/chroma/` was the only in-tree vector store provider.
- `src/cerebro/registry/indexer.py` used a FAISS-based semantic index (separate path).
- No unified provider registry/config layer existed.
- No tenant/namespace/filter contract existed across retrieval paths.
- No production runbook existed for backend selection or rollback.

**State at v0.2 (2026-04-19) — current:**

- 5 vector store providers: `chroma` (dev), `pgvector`, `qdrant`, `azure_search`, `opensearch`.
- 7 LLM providers with unified factory: `llamacpp`, `anthropic`, `azure`, `gemini`, `groq`, `openai_compatible`, `gcp`.
- `registry/indexer.py` FAISS path replaced — now uses `build_vector_store_provider()`.
- Central settings module (`settings.py`) drives all provider selection via env vars.
- Azure Pipelines CI with Postgres + NATS sidecars, Trivy, Trufflehog, load test.

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

- [x] Keep `ChromaDB` as the default local backend for one-shot development and small-scale demos.
- [x] Harden the Chroma adapter: structured logging, `development_only: true` in `get_backend_info()`, exception propagation.

### Production backends

- [x] **Priority 1: pgvector** — `providers/pgvector/` — HNSW index, idempotent upsert, namespace isolation, score normalisation, bootstrap SQL, export.
- [x] **Priority 2: Qdrant** — `providers/qdrant/` — collection bootstrap, UUID5 ID mapping, payload filters, cosine search, full export with embeddings.
- [x] **Priority 3: OpenSearch / Elasticsearch** — `providers/opensearch/` — knn_vector HNSW, bool+knn+filter query, hybrid search via `query_text` kwarg, ES 8.x compat mode, `delete_by_query`.
- [x] **Priority 4 (bonus): Azure AI Search** — `providers/azure_search/` — HNSW index bootstrap, OData filters, namespace isolation, content-only export.
- [ ] **Priority 5: Weaviate** — optional enterprise backend; deferred until concrete adoption need.

### Existing optional cloud path

- [x] GCP/Vertex path kept as optional adapter in `providers/gcp/`.
- [x] Core `VectorStoreProvider` interface is cloud-neutral; Vertex is not the default.

---

## 4. Nix Dependency Mapping

Python packages in `pyproject.toml` (runtime groups):

- [x] `psycopg` — pgvector backend
- [x] `qdrant-client` — Qdrant backend
- [x] `opensearch-py` — OpenSearch backend
- [x] `azure-search-documents` — Azure AI Search backend
- [ ] `weaviate-client` — pending Weaviate provider

Nix dev shell backend tracks (`flake.nix`):

- [ ] `.#rag-pgvector` — includes `postgresql` + `python313Packages.psycopg`
- [ ] `.#rag-qdrant` — includes `qdrant` + `python313Packages."qdrant-client"`
- [ ] `.#rag-opensearch` — includes `opensearch` + `python313Packages."opensearch-py"`
- [ ] Verify Weaviate server packaging in `nixpkgs` before adding `.#rag-weaviate`

---

## 5. Architecture

### 5.1 Vector store contract

- [x] `VectorStoreProvider` extended with: namespaces, upsert semantics, metadata filters, score threshold, backend info, `initialize_schema()` bootstrap hook, `export_documents()` migration hook.
- [x] `VectorSearchResult` typed dataclass — no raw dict passing in retrieval results.
- [x] `StoredVectorDocument` typed dataclass for migration payloads.
- [ ] Canonical metadata schema fully enforced — fields `content_hash`, `ingested_at`, `chunk_id`, `backend_namespace` not yet populated consistently across all ingestion paths.

### 5.2 Provider registry and settings

- [x] `src/cerebro/settings.py` — central env-driven config for all providers (`CEREBRO_VECTOR_STORE_PROVIDER`, `CEREBRO_VECTOR_STORE_URL`, `CEREBRO_VECTOR_STORE_NAMESPACE`, plus backend-specific keys).
- [x] `src/cerebro/providers/vector_store_factory.py` — explicit factory; no implicit defaulting.
- [x] `src/cerebro/providers/llm_factory.py` — unified LLM provider factory driven by `CEREBRO_LLM_PROVIDER`.
- [ ] CLI commands not yet wired to factory for provider introspection (see §9).
- [ ] Dashboard backend selector not yet surfaced.

### 5.3 Semantic paths unification

- [x] `registry/indexer.py` FAISS path replaced by `build_vector_store_provider()` — provider-backed.
- [x] Capability drift eliminated: `engine.py` and `indexer.py` both use `VectorStoreProvider`.
- [x] Single-type filters pushed down to the vector store in `semantic_query()` to avoid over-fetching.
- [x] Multi-type and project filters remain as post-retrieval pass (OR semantics, not universally supported at storage layer).

---

## 6. Provider Implementation

### 6.1 Chroma

- [x] Structured logging throughout (`logger.exception`, `logger.warning`).
- [x] Exception propagation — failures are raised, not swallowed as empty results.
- [x] Collection bootstrap via `get_or_create_collection`.
- [x] `development_only: true` and `production_ready: false` in `get_backend_info()`.

### 6.2 pgvector

- [x] `src/cerebro/providers/pgvector/` — full implementation with `psycopg`.
- [x] Connection bootstrap, `CREATE EXTENSION vector`, table/index creation via `bootstrap.sql` template.
- [x] Idempotent upsert by `document_id` (`ON CONFLICT DO UPDATE`).
- [x] Metadata filtering via `jsonb_extract_path_text`.
- [x] Namespace-scoped delete, clear, count.
- [x] Similarity search with cosine score normalisation `[0, 1]`.
- [x] `export_documents()` with embeddings for migration.
- [ ] `cerebro rag backend migrate` CLI command for schema migrations.

### 6.3 Qdrant

- [x] `src/cerebro/providers/qdrant/` — full implementation with `qdrant-client`.
- [x] Collection bootstrap (COSINE/HNSW). Skips creation if collection exists.
- [x] String IDs → deterministic UUID5 point IDs; original ID preserved in payload.
- [x] Payload filter builder (`FieldCondition` + `MatchValue`).
- [x] Namespace-scoped clear via `FilterSelector`; full clear via drop+recreate.
- [x] Full export with stored embeddings via `scroll`.
- [ ] Operational runbook (snapshot, restore, collection migration).

### 6.4 OpenSearch / Elasticsearch

- [x] `src/cerebro/providers/opensearch/` — native implementation with `opensearch-py`; the deprecated LangChain `elasticsearch_store.py` is superseded.
- [x] Index bootstrap: `knn_vector` HNSW cosinesimil (OpenSearch); `dense_vector` (ES 8.x compat via `OPENSEARCH_ES_COMPAT=true`).
- [x] Idempotent upsert via bulk `_op_type: index`.
- [x] Dense search: `bool + knn + filter` (all OpenSearch 2.x versions).
- [x] Hybrid search: `bool + knn + match` activated via `OPENSEARCH_ENABLE_HYBRID=true` when `query_text` in kwargs.
- [x] Score normalisation: cosinesimil `[0, 2]` → `[0, 1]` (÷2); `min_score` scaled accordingly.
- [x] Namespace-scoped `delete_by_query`; full clear via index drop+recreate.
- [ ] Operational runbook (snapshot repository, index backup, rollback).

### 6.5 Azure AI Search

- [x] `src/cerebro/providers/azure_search/` — full implementation with `azure-search-documents`.
- [x] Index bootstrap: HNSW via `HnswAlgorithmConfiguration` + `VectorSearchProfile`.
- [x] Filterable fields: `namespace`, `repo`, `source`, `git_commit`, `title` (OData term filters).
- [x] `VectorizedQuery` for dense search; OData filter composition for namespace + metadata.
- [x] Content-only export (Azure Search does not return stored vectors via search API — documented).
- [ ] Operational runbook (index backup, rollback, namespace audit).

### 6.5 Weaviate

- [ ] `src/cerebro/providers/weaviate/` — not started; deferred.
- [ ] Decide on external cluster vs. in-tree Nix package.
- [ ] Collection/class bootstrap, object upsert, hybrid filters, health checks.

---

## 7. Retrieval and Ranking

- [x] Metadata-aware filters implemented in all 5 backends.
- [x] Namespace-aware retrieval in all 5 backends.
- [x] Hybrid search available in OpenSearch (dense + BM25); other backends dense-only.
- [x] Score normalisation per backend — all return `[0, 1]`.
- [ ] Chunk provenance in citations — answers reference title/source but not stable `chunk_id`.
- [ ] Grounded generation refusal — `RigorousRAGEngine` should return an explicit no-context signal rather than a hallucinated answer when retrieval returns zero useful results.

---

## 8. Ingestion

- [x] Idempotent ingestion — all backends implement upsert semantics.
- [ ] Content hashing — skip re-embedding unchanged chunks (`content_hash` field not yet populated or checked).
- [ ] Stale chunk deletion — no handling for renamed or removed source files.
- [ ] Batch sizing policy per backend (current: fixed batch sizes in callers).
- [ ] Backend-specific ingestion metrics (accepted / skipped / updated / failed / latency).
- [ ] Dry-run mode for ingestion planning.

---

## 9. API / CLI / Dashboard

- [ ] `cerebro rag backends list` — list all registered provider aliases.
- [ ] `cerebro rag backend info` — show active backend config and capabilities.
- [ ] `cerebro rag backend health` — run health check against active backend.
- [ ] `cerebro rag backend init` — bootstrap schema for active backend.
- [ ] `cerebro rag backend migrate` — run migration/index update.
- [ ] Expose backend name, namespace, document count, filter support in `/rag/status` fully.
- [ ] Surface active backend in dashboard Control Plane panel.
- [ ] Project-scoped chat requests respect namespace in semantic retrieval.

---

## 10. Observability and Operations

- [x] Structured logging in all providers (`logging` module, no `print()` calls).
- [ ] Formal k8s readiness / liveness probes per backend.
- [ ] Latency histograms and failure counters per provider (OpenTelemetry / Prometheus).
- [ ] Index / collection size reporting in `/rag/status` for all backends.
- [ ] Migration runbooks per production backend:
  - [ ] pgvector — logical backup, schema migration, rollback
  - [ ] Qdrant — snapshot policy, collection clone, rollback
  - [ ] OpenSearch — snapshot repository, index backup, rollback
  - [ ] Azure AI Search — index export, rollback via index alias
- [ ] Backup/restore guidance in `docs/`.

---

## 11. Security

- [x] All backend credentials passed via environment variables; no hardcoded secrets.
- [x] SOPS + age encryption for secrets at rest (`sops-nix` integration).
- [x] Trufflehog + Trivy scanning in CI pipeline.
- [x] OpenSearch provider respects `OPENSEARCH_USERNAME`/`OPENSEARCH_PASSWORD` and `OPENSEARCH_API_KEY`.
- [ ] TLS enforcement for remote backends (OpenSearch has SSL detection; others need explicit guidance).
- [ ] Namespace isolation documented for multi-tenant deployments.
- [ ] Metadata field audit — ensure no sensitive path or credential material leaks into indexes.
- [ ] Audit guidance for delete requests and data retention windows.

---

## 12. Nix / Flake

- [ ] Backend-specific dev shells in `flake.nix`:
  - [ ] `.#rag-pgvector` — `postgresql` + `psycopg`
  - [ ] `.#rag-qdrant` — `qdrant` + `qdrant-client`
  - [ ] `.#rag-opensearch` — `opensearch` + `opensearch-py`
- [ ] Default shell remains lightweight and local-first (no heavy backend deps).
- [ ] Each optional backend shell declares only the dependencies it needs.
- [ ] CI integration test jobs use `nix develop .#rag-<backend> --command pytest tests/integration`.

---

## 13. Testing

### Unit tests

- [x] `test_pgvector_provider.py` — pgvector contract tests.
- [x] `test_vector_store_factory.py` — factory alias resolution.
- [x] `test_rag_engine_new_providers.py` — RAG engine with pluggable provider.
- [ ] Provider contract tests for Qdrant, OpenSearch, Azure AI Search (same fixture set as pgvector).
- [ ] Serialization/filter mapping tests for canonical metadata schema.
- [ ] Engine tests for edge cases: empty context, backend failure, namespace mismatch, duplicate upsert.

### Integration tests

- [ ] Integration suites per backend, gated behind Nix dev shells and `CEREBRO_RUN_INTEGRATION=1` env flag.
- [ ] Each suite covers: bootstrap, ingest, query, filtered query, re-ingest (idempotency), delete, health check.

### Performance tests

- [ ] Ingestion throughput benchmark by backend.
- [ ] Query latency p50/p95 by backend.
- [ ] Recall quality with shared corpus and query set.
- [ ] Regression budget so new backends don't degrade local Chroma mode.

---

## 14. Rollout Plan

### Phase 0: Contract hardening ✅

- [x] `VectorStoreProvider` v2 with typed results, namespaces, upsert, health, export.
- [x] Provider factory + central settings.
- [x] Semantic filter alignment (`KnowledgeIndexer` push-down).
- [ ] Grounded/no-context refusal in `RigorousRAGEngine` — still pending.

### Phase 1: First production backend ✅ (code complete)

- [x] `pgvector` implemented.
- [ ] Nix dev shell, integration tests, operational runbook — pending.

### Phase 2: Dedicated vector DB backend ✅ (code complete)

- [x] `Qdrant` implemented.
- [ ] Integration tests, operational runbook — pending.

### Phase 3: Hybrid search backend ✅ (code complete)

- [x] `OpenSearch` implemented with hybrid search (dense + BM25) and ES 8.x compat.
- [ ] Integration tests, operational runbook — pending.

### Phase 3b: Cloud vector search backend ✅ (code complete, bonus)

- [x] `Azure AI Search` implemented.
- [ ] Integration tests, operational runbook — pending.

### Phase 4: Optional enterprise backend

- [ ] `Weaviate` — deferred. Revisit when there is a concrete adoption need.

### Phase 5: Production polish

- [ ] Nix dev shells per backend track.
- [ ] Integration test suites gated behind backend shells.
- [ ] Provider contract tests for all backends.
- [ ] CLI `cerebro rag backends` introspection commands.
- [ ] Observability: latency histograms, liveness probes.
- [ ] Operational runbooks and backup/restore guidance.
- [ ] Dashboard Control Plane backend surface.

---

## 15. Definition of Done

A backend is production-ready when **all** of the following are true:

| Criterion | chroma | pgvector | qdrant | opensearch | azure_search |
|-----------|:------:|:--------:|:------:|:----------:|:------------:|
| Selected via shared factory/config | ✅ | ✅ | ✅ | ✅ | ✅ |
| Ingestion is idempotent | ✅ | ✅ | ✅ | ✅ | ✅ |
| Metadata filters work | ✅ | ✅ | ✅ | ✅ | ✅ |
| Namespaces work | ✅ | ✅ | ✅ | ✅ | ✅ |
| Health check returns actionable detail | ✅ | ✅ | ✅ | ✅ | ✅ |
| Integration tests pass in Nix shell | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Benchmark data exists | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Operational runbook exists | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Rollback procedure exists | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Docs state when to choose / not choose | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

`chroma` is intentionally development-only and exempt from the integration test, benchmark, and runbook criteria.

---

## 16. Recommended Next Steps

Priority order based on Definition of Done gaps:

1. **Nix dev shells** (§12) — unblocks CI integration tests for pgvector, Qdrant, OpenSearch.
2. **Provider contract tests** (§13) — Qdrant, OpenSearch, Azure Search missing test coverage.
3. **CLI `cerebro rag backends`** (§9) — list, info, health introspection.
4. **Grounded/no-context refusal** (§14 Phase 0) — last remaining Phase 0 item.
5. **Operational runbooks** (§10) — required for Definition of Done on all production backends.
6. **Content hashing** (§8) — skip re-embedding unchanged chunks.
7. **Weaviate** (§6.5) — only if a concrete adoption need materialises.
