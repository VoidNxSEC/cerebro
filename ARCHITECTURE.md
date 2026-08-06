# Architecture

## System Purpose

CEREBRO is a hermetic code-intelligence and distributed Retrieval-Augmented Generation (RAG)
platform. It performs deep Abstract Syntax Tree analysis over source code, indexes the result
into a pluggable vector store, and answers grounded queries with citations. The design goal is
that it runs identically on a laptop and on Kubernetes, with LLM and vector-store providers
swappable by configuration rather than by code change.

It is also the measurement instrument for the VoidNX Labs ecosystem: `cerebro metrics scan`
produces the repository health data that drives the platform's portfolio and state documents.

## High-Level Overview

```
┌────────────────────────────────────────────────────────┐
│ Interfaces                                             │
│   Rich CLI  ·  Textual TUI  ·  React dashboard :18321  │
└───────────────────────┬────────────────────────────────┘
                        ▼
┌────────────────────────────────────────────────────────┐
│ core/                                                  │
│   HermeticAnalyzer (Tree-sitter AST)                   │
│   MetricsCollector  → metrics_profiles rubric          │
│   RAG engine, chunking, embedding                      │
└───────┬─────────────────────────────┬──────────────────┘
        ▼                             ▼
┌────────────────┐            ┌───────────────────┐
│ providers/     │            │ registry/         │
│ llama.cpp      │            │ vector stores:    │
│ Azure OpenAI   │            │ ChromaDB          │
│ Vertex AI      │            │ Elasticsearch     │
└────────────────┘            │ PGVector          │
                              └───────────────────┘
                        │
                        ▼
              adr-ledger/knowledge/knowledge_base.json
```

## Components

| Package | Files | Responsibility |
|---|---|---|
| `src/cerebro/core/` | 30 | Analyzer, RAG engine, metrics collector, scoring rubric |
| `src/cerebro/providers/` | 30 | LLM provider adapters behind a common interface |
| `src/cerebro/modules/` | 10 | Feature modules |
| `src/cerebro/tui/` | 8 | Textual terminal interface |
| `src/cerebro/commands/` | 7 | CLI command surface |
| `src/cerebro/nats/` | 6 | Event mesh publication and subscription |
| `src/cerebro/intelligence/` | 5 | Briefing, analysis, synthesis |
| `src/cerebro/registry/` | 3 | Vector-store and provider registries |
| `src/cerebro/interfaces/` | 3 | Interface contracts |
| `src/cerebro/api/` | 2 | HTTP API surface |
| `src/cerebro/services/` | 2 | Long-running services |

### Metrics subsystem

`core/metrics_collector.py` and `core/metrics_profiles.py` implement zero-token repository
analysis. They separate four concepts that are easy to conflate:

- **Measurement** — LoC split into authored / vendored / generated / docs / config buckets,
  enumerated from `git ls-files` so ignored files never count.
- **Classification** — an `archetype` per repo (service, mcp-server, cli-tool, library,
  infra-config, knowledge-base, frontend, docs-site, research).
- **Position** — a `stack_layer` per repo (backbone, inference, rag, agents-os, security, dev,
  frontend, docs).
- **Evaluation** — eleven dimensions scored, weighted per `archetype × stack_layer`, where a
  dimension may be **N/A** rather than zero. A docs site is not judged for lacking tests.

## Data Flow

**Ingestion:** source → `HermeticAnalyzer` (Tree-sitter AST) → semantic chunking → embeddings
via the configured provider → vector store via the configured registry.

**Query:** natural-language question → embedding → vector search → cross-encoder reranking →
LLM generation with source citations.

**Metrics:** `discover_repos()` → per-repo collectors (code, git, deps, quality, security,
architecture, interface) → classification → per-profile scoring → cross-repo centrality pass →
snapshot written to `data/metrics/`.

## Trust Boundaries

| Boundary | Control |
|---|---|
| MCP client → cerebro | reached only via securellm-mcp, itself behind the bridge |
| cerebro → LLM provider | provider adapter; local llama.cpp requires no egress |
| cerebro → vector store | configured backend, local by default |
| Metrics collector → filesystem | read-only; git-tracked files only |

Local-first is the default posture: with `llama.cpp` and ChromaDB configured, no request
leaves the host.

## Runtime Model

Python 3.13. CLI and TUI are synchronous entry points; the API service is async. The metrics
collector is deliberately synchronous and token-free — it shells out to `git` and reads files,
consuming no LLM budget.

## Configuration

Environment-driven. `CEREBRO_LLM_PROVIDER` selects the LLM adapter; `CEREBRO_ARCH_PATH`
selects the workspace root the metrics collector scans (default `~/master`). See `config/`.

## Storage

- Vector store: ChromaDB (local), Elasticsearch or PGVector, selected by registry.
- Metrics: `data/metrics/metrics_snapshot.json` plus timestamped history under
  `data/metrics/history/`.
- Knowledge base: reads `adr-ledger/knowledge/knowledge_base.json`.

## External Integrations

| Target | Purpose | Required |
|---|---|---|
| llama.cpp :8081 | local inference and embeddings | no |
| Azure OpenAI / Vertex AI | cloud inference | no |
| NATS :4222 | event publication | no |
| adr-ledger | ADR knowledge corpus | for governance queries |
| BigQuery | billing export driving budget caps | no |

## Security Model

- No credentials in the repository; provider keys come from the environment.
- Local-first default means the sensitive path requires no outbound network.
- Metrics collection reads only git-tracked files and never executes repository code.
- Security findings in the metrics scanner are entropy-gated and language-scoped to avoid
  flagging schema field names as secrets.

## Testing Model

37 test files under `tests/`, including `tests/integration/`. `nix develop` then `pytest`.
Cost governance is exercised through `CerebroCreditValidator`.

## Operational Notes

- Health probe, Prometheus metrics endpoint, graceful shutdown, container restart policy.
- Runs from `deploy/docker-compose.master.yml` on port 8009.
- `charts/` holds Kubernetes manifests; `cloud/` holds cloud-specific configuration.
- Build: `nix develop` then the CLI is on `$PATH` as `cerebro`.

## Known Architectural Risks

1. **The flake exposes no `packages`, `checks` or `apps` outputs** — reproducibility scores 70
   where sibling services reach 88–94. The dev shell works; the build contract is incomplete.
2. **No `ARCHITECTURE.md`-level record of the provider abstraction's invariants.** Adding a
   provider currently means reading 30 files to infer the contract.
3. **No `SECURITY.md` or threat model**, despite handling credentials for three cloud
   providers.
4. **No operational runbook.**
5. **Metrics rubric weights are hand-tuned.** They encode a defensible judgement about what
   matters per archetype, but they are not empirically calibrated and should be revisited when
   the ecosystem shape changes.
6. **`legacy/` still present** (2 files) — migration not finished.
