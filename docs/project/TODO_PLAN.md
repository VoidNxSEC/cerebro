# Cerebro RAG Production Expansion TODO

**Last updated:** 2026-04-24
**Scope:** Extend Cerebro from a local-first RAG stack into a production-ready, multi-backend retrieval platform.

---

## Changelog

| Version | Date | Summary |
|---------|------|---------|
| v0.1 | 2026-04-08 | Initial planning document |
| v0.2 | 2026-04-19 | Audit pass — mark completed work; align with actual codebase state |
| v0.3 | 2026-04-19 | Weaviate provider; all 4 Nix backend dev shells; weaviate poetry group |
| v0.4 | 2026-04-21 | Canonical metadata schema; API /rag/backends + enriched /rag/status; 5 operational runbooks |
| v0.5 | 2026-04-24 | 4 new runbooks (LLM providers, RAG pipeline, backend selection, reranker); fix §9/§12 status; dep upgrades |
| v0.6 | 2026-04-24 | Strategic pivot: distributed platform on BREV + k3s + NATS JetStream + SOPS; real integration tests replace mock contract tests |
| v0.7 | 2026-04-25 | NATS conforms to Spectre Fleet taxonomy (rag.index.v1, document.indexed.v1); integration test suite; .#brev-deploy shell; Helm chart (charts/cerebro/); registered in spectre/apps/cerebro-rag/ |

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

**State at v0.3 (2026-04-19) — current:**

- 6 vector store providers: added `weaviate` — cloud-native, local-first, hybrid BM25+vector.
- All 4 backend Nix dev shells added: `.#rag-pgvector`, `.#rag-qdrant`, `.#rag-opensearch`, `.#rag-weaviate`.
- Per-backend Poetry optional groups: `rag-pgvector`, `rag-qdrant`, `rag-opensearch`, `rag-azure-search`, `rag-weaviate`.

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
- [x] **Priority 5: Weaviate** — `providers/weaviate/` — HNSW COSINE, UUID5 mapping, property filters, hybrid BM25+vector, full export with vectors.

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
- [x] `weaviate-client` — Weaviate backend (`rag-weaviate` Poetry group)

Nix dev shell backend tracks (`flake.nix`):

- [x] `.#rag-pgvector` — includes `postgresql` + `python313Packages.psycopg`
- [x] `.#rag-qdrant` — includes `qdrant` + `python313Packages."qdrant-client"`
- [x] `.#rag-opensearch` — includes `opensearch` + `python313Packages."opensearch-py"`
- [x] `.#rag-weaviate` — includes `weaviate` + `python313Packages."weaviate-client"`

---

## 5. Architecture

### 5.1 Vector store contract

- [x] `VectorStoreProvider` extended with: namespaces, upsert semantics, metadata filters, score threshold, backend info, `initialize_schema()` bootstrap hook, `export_documents()` migration hook.
- [x] `VectorSearchResult` typed dataclass — no raw dict passing in retrieval results.
- [x] `StoredVectorDocument` typed dataclass for migration payloads.
- [x] Canonical metadata schema enforced — `core/metadata.py` defines `CANONICAL_FIELDS` and `build_canonical_fields()`; both `engine._normalize_document()` and `indexer._item_to_document()` populate `content_hash`, `ingested_at`, `chunk_id`, `backend_namespace`, `_cerebro_schema_version` on every ingestion.

### 5.2 Provider registry and settings

- [x] `src/cerebro/settings.py` — central env-driven config for all providers (`CEREBRO_VECTOR_STORE_PROVIDER`, `CEREBRO_VECTOR_STORE_URL`, `CEREBRO_VECTOR_STORE_NAMESPACE`, plus backend-specific keys).
- [x] `src/cerebro/providers/vector_store_factory.py` — explicit factory; no implicit defaulting.
- [x] `src/cerebro/providers/llm_factory.py` — unified LLM provider factory driven by `CEREBRO_LLM_PROVIDER`.
- [x] CLI commands wired to factory — `cerebro rag backends list`, `cerebro rag backend info/health/init/smoke/migrate` all route through `build_vector_store_provider()`.
- [x] Dashboard backend selector — `GET /rag/backends` returns all backends with capabilities (`supports_filters`, `supports_hybrid`, `production_ready`, `active`); `GET /rag/status` enriched with `available_backends`, `supports_hybrid`, `supports_filters`, `schema_version`.

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
- [x] Operational runbook — `docs/guides/runbooks/qdrant.md` (snapshot, restore, migration, rollback).

### 6.4 OpenSearch / Elasticsearch

- [x] `src/cerebro/providers/opensearch/` — native implementation with `opensearch-py`; the deprecated LangChain `elasticsearch_store.py` is superseded.
- [x] Index bootstrap: `knn_vector` HNSW cosinesimil (OpenSearch); `dense_vector` (ES 8.x compat via `OPENSEARCH_ES_COMPAT=true`).
- [x] Idempotent upsert via bulk `_op_type: index`.
- [x] Dense search: `bool + knn + filter` (all OpenSearch 2.x versions).
- [x] Hybrid search: `bool + knn + match` activated via `OPENSEARCH_ENABLE_HYBRID=true` when `query_text` in kwargs.
- [x] Score normalisation: cosinesimil `[0, 2]` → `[0, 1]` (÷2); `min_score` scaled accordingly.
- [x] Namespace-scoped `delete_by_query`; full clear via index drop+recreate.
- [x] Operational runbook — `docs/guides/runbooks/opensearch.md` (snapshot repo, index alias rollback, hybrid search).

### 6.5 Azure AI Search

- [x] `src/cerebro/providers/azure_search/` — full implementation with `azure-search-documents`.
- [x] Index bootstrap: HNSW via `HnswAlgorithmConfiguration` + `VectorSearchProfile`.
- [x] Filterable fields: `namespace`, `repo`, `source`, `git_commit`, `title` (OData term filters).
- [x] `VectorizedQuery` for dense search; OData filter composition for namespace + metadata.
- [x] Content-only export (Azure Search does not return stored vectors via search API — documented).
- [x] Operational runbook — `docs/guides/runbooks/azure_search.md` (schema export, alias rollback, namespace audit).

### 6.6 Weaviate

- [x] `src/cerebro/providers/weaviate/` — full implementation with `weaviate-client>=4.9`.
- [x] `pkgs.weaviate` server in `.#rag-weaviate` Nix shell — local-first, no cloud required.
- [x] Collection bootstrap: COSINE HNSW via `Configure.VectorIndex.hnsw`, bring-your-own-vectors mode.
- [x] UUID5 ID mapping; original ID preserved in `_cerebro_id` property.
- [x] Property-based filters: `namespace`, `source`, `title`, `repo`, `git_commit`, `_cerebro_id`.
- [x] Dense search: `near_vector` with certainty-based score in `[0, 1]`.
- [x] Hybrid search: `query.hybrid()` (BM25 + vector RRF) via `WEAVIATE_ENABLE_HYBRID=true` + `query_text` kwarg.
- [x] Full export with stored vectors via `fetch_objects(include_vector=True)`.
- [x] Operational runbook — `docs/guides/runbooks/weaviate.md` (backup, restore, multi-tenancy, hybrid, rollback).

---

## 7. Retrieval and Ranking

- [x] Metadata-aware filters implemented in all 5 backends.
- [x] Namespace-aware retrieval in all 5 backends.
- [x] Hybrid search available in OpenSearch and Weaviate (BM25 + vector); other backends dense-only.
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

- [x] `cerebro rag backends list` — list all registered provider aliases.
- [x] `cerebro rag backend info` — show active backend config and capabilities.
- [x] `cerebro rag backend health` — run health check against active backend.
- [x] `cerebro rag backend init` — bootstrap schema for active backend.
- [x] `cerebro rag backend migrate` — run migration/index update.
- [x] Expose backend name, namespace, document count, filter support in `/rag/status` fully.
- [ ] Surface active backend in dashboard Control Plane panel (UI component — API already exposes `/rag/backends`).
- [ ] Project-scoped chat requests respect namespace in semantic retrieval.

---

## 10. Observability and Operations

- [x] Structured logging in all providers (`logging` module, no `print()` calls).
- [ ] Formal k8s readiness / liveness probes per backend.
- [ ] Latency histograms and failure counters per provider (OpenTelemetry / Prometheus).
- [ ] Index / collection size reporting in `/rag/status` for all backends.
- [x] Operational runbooks per production backend (`docs/guides/runbooks/`):
  - [x] pgvector — logical backup, HNSW index rebuild, WAL/pgBackRest, rollback
  - [x] Qdrant — snapshot create/restore, collection migration, rollback
  - [x] OpenSearch — snapshot repository (fs/S3), index alias rollback, hybrid search
  - [x] Azure AI Search — index schema export, alias rollback, namespace audit
  - [x] Weaviate — backup (fs/S3), restore, multi-tenancy, hybrid search, rollback
- [x] Cross-cutting operational runbooks:
  - [x] `llm_providers.md` — 7 LLM backends (llamacpp, anthropic, gemini, groq, azure, openai_compatible, gcp)
  - [x] `rag_pipeline.md` — end-to-end ingestion/query/rerank operations
  - [x] `backend_selection.md` — decision tree for choosing vector store
  - [x] `reranker.md` — `cerebro-reranker` sidecar, fallback, NATS future path
- [x] Backup/restore guidance folded into per-backend runbooks (§3–4 of each).

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

- [x] Backend-specific dev shells in `flake.nix`:
  - [x] `.#rag-pgvector` — `postgresql` + `psycopg`
  - [x] `.#rag-qdrant` — `qdrant` + `qdrant-client`
  - [x] `.#rag-opensearch` — `opensearch` + `opensearch-py`
  - [x] `.#rag-weaviate` — `weaviate` + `weaviate-client`
- [x] Default shell remains lightweight and local-first (no heavy backend deps).
- [x] Each optional backend shell declares only the dependencies it needs.
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

### Phase 4: Cloud-native local-first backend ✅ (code complete)

- [x] `Weaviate` implemented — HNSW COSINE, hybrid BM25+vector, local Nix shell.

### Phase 5: Production polish

- [x] Nix dev shells per backend track — `.#rag-pgvector`, `.#rag-qdrant`, `.#rag-opensearch`, `.#rag-weaviate`.
- [ ] Integration test suites gated behind backend shells.
- [ ] Provider contract tests for all backends.
- [ ] CLI `cerebro rag backends` introspection commands.
- [ ] Observability: latency histograms, liveness probes.
- [ ] Operational runbooks and backup/restore guidance.
- [ ] Dashboard Control Plane backend surface.

---

## 15. Definition of Done

A backend is production-ready when **all** of the following are true:

| Criterion | chroma | pgvector | qdrant | opensearch | azure_search | weaviate |
|-----------|:------:|:--------:|:------:|:----------:|:------------:|:--------:|
| Selected via shared factory/config | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Ingestion is idempotent | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Metadata filters work | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Namespaces work | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Health check returns actionable detail | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Nix dev shell exists | ⬜ | ✅ | ✅ | ✅ | ⬜ | ✅ |
| Integration tests pass in Nix shell | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Benchmark data exists | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Operational runbook exists | ⬜ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rollback procedure exists | ⬜ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Docs state when to choose / not choose | ✅* | ✅ | ✅ | ✅ | ✅ | ✅ |

`chroma` is intentionally development-only and exempt from the Nix shell, integration test, benchmark, and runbook criteria. (*) `backend_selection.md` documents when to choose/not choose it.
`azure_search` has no Nix server package — use the Azure-hosted service directly.

---

## 16. Recommended Next Steps

**Strategic pivot (v0.6):** Cerebro is being repositioned from a single-node RAG
platform to a distributed GPU-orchestrated system running on rented Nvidia BREV
nodes joined into a k3s cluster. Mock-based provider contract tests are
de-prioritized in favor of real end-to-end integration tests.

### Active workstream: Distribution (Phase 6) — status

1. **NATS JetStream ingestion stream** ✅ — `src/cerebro/nats/` conforms to
   Spectre Fleet taxonomy: `rag.index.v1` (ingest), `document.indexed.v1.<correlation_id>`
   (completion). Spectre envelope: `event_id`, `event_type`, `correlation_id`,
   `source_service`, `timestamp`, `payload`, `metadata`.
2. **Real integration test via NATS** ✅ — `tests/integration/test_nats_ingest_query.py`
   (5 tests: publish+complete, query-after-ingest, idempotency, bad-embedding error,
   namespace cleanup). Gated by `CEREBRO_RUN_INTEGRATION=1`.
3. **`.#brev-deploy` dev shell** ✅ — `flake.nix` shell with `kubectl`, `kubernetes-helm`,
   `kubeseal`, `k3sup`, `k9s`, `brev-cli`, plus usage instructions in hook.
4. **Helm chart** ✅ — `charts/cerebro/` with deployments for api, ingest-worker,
   reranker; NATS as sub-chart dependency; `values-dev.yaml` and `values-prod.yaml`
   (GPU nodeSelector for reranker on BREV nodes). `helm lint` passes (0 failures).
5. **Spectre registration** ✅ — `spectre/apps/cerebro-rag/README.md` documents
   the integration contract and points to the Python service.

### Deferred (low-priority mock work)

- Provider contract tests for Azure Search and Weaviate (pgvector, qdrant,
  opensearch already covered). Real integration tests will supersede these.

### Other gaps (unchanged priority)

- **Grounded/no-context refusal** (§14 Phase 0) — `RigorousRAGEngine` should
  return explicit no-context signal.
- **Content hashing dedup** (§8) — use `content_hash` to skip re-embedding.
- **Dashboard backend selector UI** — consume `GET /rag/backends` in Control Plane.
- **Agent pipeline primitives** — structured multi-step agent flows.

---

## 17. Phase 6 — Distribution (BREV + k3s + NATS)

### Stack decisions

| Layer | Pick | Rationale |
|-------|------|-----------|
| GPU compute | Nvidia BREV SSH-joined k3s workers | BREV exposes SSH + kubeconfig; ephemeral nodes join via `k3s agent --token ...`. No need for EKS/GKE overhead. |
| Orchestration | k3s + Helm chart per service | Lightweight, fits ephemeral BREV nodes. |
| Inter-node data | NATS JetStream (already in `src/cerebro/nats/`) | Persistent streams, consumer groups, at-least-once. Use for ingestion events, embedding jobs, query fanout, reranker offload. |
| Secrets | SOPS (age) + `kubeseal` → SealedSecrets | Nix renders SealedSecret manifest at deploy time; no plain secrets in git or env files. |
| Build | Nix `dockerTools.buildLayeredImage` | Reproducible OCI images, no Dockerfiles, pinned to flake.lock. |
| Deploy shell | `.#brev-deploy` | Bundles tooling + wrapper scripts. |

### Advanced inter-node tech (optional, later)

- **Ray** — distributed embeddings across GPU pods when NATS consumer groups
  aren't expressive enough (heterogeneous compute, object spill).
- **NCCL** — multi-GPU collective ops inside a single reranker pod.
- **Arrow Flight** — large vector transfers between backends during migration.

NATS JetStream covers 80% of the real need; introduce Ray/NCCL/Flight only when
a specific workload hits NATS limits.

### Phase 6 success criteria

- [x] NATS module conforms to Spectre Fleet taxonomy
- [x] Integration test suite exists and skips gracefully without a live cluster
- [x] `.#brev-deploy` shell provides kubectl, helm, kubeseal, k3sup, k9s, brev-cli
- [x] Helm chart lints clean; GPU nodeSelector in `values-prod.yaml`
- [x] Cerebro registered in `spectre/apps/cerebro-rag/`
- [ ] `nix develop .#brev-deploy --command helm upgrade --install cerebro ...` deploys to a live k3s cluster
- [ ] `CEREBRO_RUN_INTEGRATION=1 pytest tests/integration/test_nats_ingest_query.py` passes against deployed cluster
- [ ] A BREV GPU node joins k3s via `k3sup join` and reranker schedules on it
