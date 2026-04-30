# Feature Matrix

Honest status of every major feature. Each entry includes how to verify it and what it requires.

| Feature | Status | Verify with | Requires |
|---------|--------|-------------|----------|
| RAG ingest | ✅ Works offline | `cerebro rag ingest ./data/analyzed/all_artifacts.jsonl` | none |
| RAG query + grounded generation | ✅ Works offline | `cerebro rag query "your question"` | LLM provider |
| Content hash dedup on ingest | ✅ Implemented | Ingest a file twice — logs show `X duplicates skipped` | none |
| Grounded refusal (relevance gate 0.25) | ✅ Implemented | `cerebro test grounded-search "unrelated question"` → `no_context: true` | LLM provider |
| Multi-backend vector stores | ✅ Code exists | Set `CEREBRO_VECTOR_STORE_PROVIDER=qdrant` (or chroma, weaviate, opensearch, pgvector, azure-ai-search) | Each backend running |
| Reranker — HybridEngine (MiniLM → Electra → DeBERTa) | ✅ Works | Start `cerebro-reranker` on port 8090; `cerebro rag rerank` uses it automatically | `~/master/cerebro-reranker` running |
| Backend selector dashboard | ✅ Works | `cerebro dashboard` → open `http://localhost:18321` → ControlPlane | none |
| TUI | ✅ Works | `cerebro tui` | none |
| CLI (all 45 commands) | ✅ Works | `cerebro --help` | varies per group |
| Knowledge extraction (AST + metadata) | ✅ Works | `cerebro knowledge analyze /path/to/repo "desc"` | none |
| Metrics scan (zero-token) | ✅ Works | `cerebro metrics scan` | none |
| NATS JetStream ingest worker | ✅ Implemented | Requires NATS server. `NATS_URL=nats://localhost:4222 cerebro rag ingest ...` | NATS 2.10+ |
| Integration test suite | ⚠️ Gated | `CEREBRO_RUN_INTEGRATION=1 pytest tests/integration/` | Live NATS + cluster |
| BREV GPU deploy | ⚠️ Shell ready, cluster needed | `nix develop .#brev-deploy` → `helm upgrade cerebro charts/cerebro/` | Physical BREV node |
| GCP Discovery Engine | ⚠️ Optional | `cerebro gcp status` (needs `GCP_PROJECT_ID`) | GCP project + billing |
| Strategy / career intelligence | ⚠️ Experimental | `cerebro strategy optimize` | LLM provider + indexed KB |
| Azure AKS deploy | ⚠️ Scripts + workflows ready | See `scripts/bootstrap-azure-aks-acr.sh` | Azure subscription |
| MkDocs documentation site | ✅ Works | `nix develop --command mkdocs serve` | none |

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ Works | Implemented, tested locally, no external infra needed (beyond the listed requirements) |
| ⚠️ Partial | Code exists and is correct but requires infrastructure not available in a local-only setup |

## Dependency Map

```
Offline-only (no env vars needed):
  cerebro knowledge analyze
  cerebro metrics scan/watch/report/compare/check
  cerebro rag ingest (chroma backend)
  cerebro tui
  cerebro dashboard (dashboard)

Needs LLM provider configured:
  cerebro rag query
  cerebro test grounded-*
  cerebro strategy *
  cerebro content *

Needs external services:
  NATS → cerebro rag ingest (NATS worker path)
  Reranker → automatic when CEREBRO_RERANKER_URL reachable
  GCP → cerebro gcp *
```
