<div align="center">

# Cerebro

**Enterprise Knowledge Extraction & Distributed RAG Platform**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg?style=flat-square)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Nix](https://img.shields.io/badge/Nix-Reproducible-5277C3?style=flat-square&logo=nixos&logoColor=white)](https://nixos.org/)
[![React](https://img.shields.io/badge/React-Dashboard-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Native-326CE5?style=flat-square&logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/VoidNxSEC/cerebro/ci.yml?branch=main&style=flat-square&label=GitHub%20Actions)](https://github.com/VoidNxSEC/cerebro/actions/workflows/ci.yml)

`v1.0.0b1` · `cerebro` CLI · Python 3.13+ · Nix-first

</div>

---

Cerebro is a modular, hermetic knowledge extraction and RAG platform. It combines deep static code analysis, retrieval-augmented generation with pluggable backends, real-time repository intelligence, and enterprise cloud integrations — all accessible through a unified triple-interface design (CLI, TUI, and web dashboard).

The runtime is built Nix-first: what runs locally runs identically in CI and on Kubernetes.

---

## Quickstart

```bash
# Enter the hermetic dev environment
nix develop

# Configure cloud and LLM settings
cerebro setup

# Ingest a codebase into the knowledge base
cerebro knowledge analyze . "Initial analysis"
cerebro rag ingest ./data/analyzed/all_artifacts.jsonl

# Query
cerebro rag query "Explain the RAG pipeline architecture"

# Launch the API-backed dashboard
cerebro dashboard
```

---

## Interfaces

Cerebro exposes three fully-featured entry points sharing the same backend:

| Interface | Command | Description |
|-----------|---------|-------------|
| **CLI** | `cerebro` / `phantom` | Typer-based CLI for automation, CI/CD, and scripting |
| **TUI** | `cerebro tui` | Textual interactive terminal UI |
| **Dashboard** | `cerebro dashboard` then open `localhost:18321` | React/Vite/TypeScript web dashboard backed by the API on `localhost:8009` |

### CLI Command Groups

45 commands across 12 groups. → [Full command reference](docs/commands/README.md) · [Feature matrix](docs/project/FEATURE_MATRIX.md)

| Group | Key commands | Requires |
|-------|-------------|---------|
| `cerebro rag` | `ingest`, `query`, `status`, `init`, `smoke`, `migrate`, `rerank` | — / LLM provider |
| `cerebro knowledge` | `analyze`, `batch-analyze`, `summarize`, `docs`, `etl` | — |
| `cerebro ops` | `health`, `status` | — |
| `cerebro metrics` | `scan`, `watch`, `report`, `compare`, `check` | — |
| `cerebro setup` | `wizard` | — |
| `cerebro test` | `grounded-search`, `grounded-gen`, `verify-api` | LLM provider |
| `cerebro content` | `mine`, `analyze` | LLM provider |
| `cerebro strategy` | `optimize`, `salary`, `moat`, `trends` | LLM provider |
| `cerebro gcp` | `status`, `create-engine`, `monitor`, `burn` | GCP credentials |

### Dashboard Pages

`Dashboard` · `Projects` · `Intelligence` · `Briefing` · `Chat` · `Metrics` · `Control Plane` · `Settings`

---

## Architecture

```mermaid
graph TD
    subgraph "Interfaces"
        CLI["CLI (Typer)"]
        TUI["TUI (Textual)"]
        DASH["Dashboard (React)"]
    end

    subgraph "API Layer"
        API["FastAPI — port 8000"]
        WS["WebSocket — real-time"]
    end

    subgraph "Core Intelligence"
        RAG["RigorousRAGEngine"]
        INTEL["CerebroIntelligence"]
        BRIEF["BriefingGenerator"]
        METRICS["MetricsCollector"]
        WATCHER["RepoWatcher"]
        RERANK["CerebroRerankerClient"]
    end

    subgraph "LLM Providers"
        LLAMA["Llama.cpp (local)"]
        AZURE_LLM["Azure OpenAI"]
        CLAUDE["Anthropic Claude"]
        GEMINI["Google Gemini"]
        GROQ["Groq"]
        OAI["OpenAI-compatible"]
        VERTEX["GCP Vertex AI"]
    end

    subgraph "Vector Store Providers"
        CHROMA["ChromaDB (dev)"]
        PG["pgvector (prod)"]
        AZSEARCH["Azure AI Search (prod)"]
    end

    subgraph "Event Bus"
        NATS["NATS JetStream"]
    end

    CLI --> API
    TUI --> API
    DASH --> API
    API --> WS

    API --> RAG
    API --> INTEL
    API --> BRIEF
    API --> METRICS
    API --> WATCHER

    RAG --> RERANK
    RAG --> CHROMA
    RAG --> PG
    RAG --> AZSEARCH

    RAG --> LLAMA
    RAG --> AZURE_LLM
    RAG --> CLAUDE
    RAG --> GEMINI
    RAG --> GROQ
    RAG --> OAI
    RAG --> VERTEX

    INTEL --> NATS
    WATCHER --> NATS
```

---

## Providers

All providers implement abstract interfaces defined in `src/cerebro/interfaces/`. Selection is driven entirely by environment variables — no code changes required to switch backends.

### LLM Providers

Set via `CEREBRO_LLM_PROVIDER`.

| Alias | Provider | Notes |
|-------|----------|-------|
| `llamacpp` | Llama.cpp | Default. Local inference, air-gapped friendly. Port 8081. |
| `anthropic` | Anthropic Claude | Requires `ANTHROPIC_API_KEY` |
| `azure` | Azure OpenAI | Requires `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` |
| `gemini` | Google Gemini | Requires `GOOGLE_API_KEY` |
| `groq` | Groq | Requires `GROQ_API_KEY` |
| `openai_compatible` | Any OpenAI-compatible endpoint | Set `OPENAI_API_BASE` |
| `gcp` / `vertex` | GCP Vertex AI | Uses Application Default Credentials |

### Vector Store Providers

Set via `CEREBRO_VECTOR_STORE_PROVIDER`.

| Alias | Provider | Production? | Notes |
|-------|----------|:-----------:|-------|
| `chroma` | ChromaDB | Dev only | Local embedded. Default. |
| `pgvector` | PostgreSQL + pgvector | Yes | Requires `CEREBRO_VECTOR_STORE_URL` (DSN). HNSW index, full namespace support, idempotent upsert. |
| `azure_search` | Azure AI Search | Yes | Requires `AZURE_SEARCH_ENDPOINT` + `AZURE_SEARCH_API_KEY`. HNSW, OData filters, namespace isolation. |

#### pgvector bootstrap

```bash
# Initialize schema (creates extension, table, indexes)
cerebro rag init

# Or via CLI flag
CEREBRO_VECTOR_STORE_PROVIDER=pgvector \
CEREBRO_VECTOR_STORE_URL=postgresql://user:pass@host/dbname \
cerebro rag init
```

#### Azure AI Search bootstrap

```bash
CEREBRO_VECTOR_STORE_PROVIDER=azure_search \
AZURE_SEARCH_ENDPOINT=https://my-service.search.windows.net \
AZURE_SEARCH_API_KEY=<key> \
cerebro rag init
```

---

## Core Intelligence Engine

### RigorousRAGEngine

The central retrieval-augmented generation engine. Features:

- Pluggable LLM and vector store via factory injection
- Multi-stage embedding (Jina → MPNET → MiniLM fallback chain)
- Namespace-scoped retrieval and ingestion
- Idempotent upsert with content hashing
- Prompt injection protection (regex heuristics + control character sanitization)
- Grounded generation — refuses to label answers as grounded when retrieval fails

---

## Deployment

Production deploy is centered on the Nix-built API image plus Kubernetes:

- Azure ACR publish: [`.github/deploy-acr.yml`](.github/deploy-acr.yml)
- Azure AKS rollout: [`.github/deploy-aks.yml`](.github/deploy-aks.yml)
- Deployment runbook: [`docs/guides/DEPLOYMENT.md`](docs/guides/DEPLOYMENT.md)

Notes:

- `cerebro dashboard` is a local developer workflow. It starts the backend on `:8009` and the Vite frontend on `:18321`.
- The deployable container serves the FastAPI API on `:8000`.
- Cloud Run remains an optional path via [`.github/deploy.yml`](.github/deploy.yml), using the repo `Dockerfile`.

### CerebroIntelligence

Hermetic static analyzer operating on codebases without executing them:

- AST-based code extraction
- Zero-token repository health scoring: **activity (30%)** + **docs (20%)** + **testing (20%)** + **security (30%)**
- Language detection: Python, Rust, TypeScript, JavaScript, Nix, Go, and more
- Dependency graph extraction (nodes + edges)

### Intelligence Registry

Dual semantic search paths:

| Path | Backend | Purpose |
|------|---------|---------|
| `core/rag/engine.py` | Pluggable vector store | RAG queries, chat, grounded generation |
| `registry/indexer.py` | FAISS | Intelligence / threat / alert search |

### BriefingGenerator

Produces AI-generated briefings from collected intelligence:

- `GET /briefing/daily` — daily summary
- `GET /briefing/executive` — executive summary with threat levels

### MetricsCollector + RepoWatcher

- Zero-token metrics: git log, filesystem, config parsing, regex security patterns
- `RepoWatcher` polls repositories every 10 seconds and broadcasts changes over WebSocket

---

## Event Bus (NATS JetStream)

Cerebro publishes and consumes events via NATS for async intelligence processing.

| Topic | Direction | Payload |
|-------|-----------|---------|
| `cognition.insight.generated.v1` | Publish | Extracted insight after code analysis |
| `ingest.file.sanitized.v1` | Subscribe | Sanitized file ready for ingestion |

Configure with `NATS_URL` (default: `nats://localhost:4222`).

---

## Security

- **SOPS + age** — secrets encrypted at rest via `sops-nix` (NixOS module)
- **Trufflehog** — git history secret scanning in CI (only-verified mode)
- **Trivy** — container image and filesystem vulnerability scanning (CRITICAL/HIGH exit-code 1)
- **Prompt injection filtering** — content validation on all RAG inputs
- **Namespace isolation** — tenant boundaries enforced at the storage layer

---

## Cloud Integration

### Azure

| Service | Usage |
|---------|-------|
| Azure OpenAI | LLM inference and embeddings |
| Azure AI Search | Production vector store with HNSW and OData filters |
| Azure Kubernetes Service (AKS) | Production workload deployment |
| Azure Container Registry (ACR) | Container image registry |
| Azure Load Testing | JMeter-based load validation (p99 < 200ms, error < 5%) |

Config snapshot: `AzureDeploymentConfig.from_env()` reads all Azure settings from environment variables. No values are hardcoded.

### GCP

| Service | Usage |
|---------|-------|
| Vertex AI Search | Optional fallback retrieval backend |
| Dialogflow CX | Conversational interface |
| BigQuery | Billing and usage analytics |
| Cloud Run | Optional serverless deployment path |
| Artifact Registry | Optional container registry path |

Config snapshot: `GcpDeploymentConfig.from_env()`.

---

## CI/CD

The active automation surface is GitHub Actions plus the checked-in GitLab CI file.

### GitHub Actions

- [`.github/ci.yml`](.github/ci.yml) runs the repo CI runner on push and pull request to `main`.
- [`.github/nix-build.yml`](.github/nix-build.yml) validates the flake build surface.
- [`.github/deploy-acr.yml`](.github/deploy-acr.yml) publishes the Nix-built API image to ACR.
- [`.github/deploy-aks.yml`](.github/deploy-aks.yml) deploys that image to AKS.
- [`.github/deploy.yml`](.github/deploy.yml) is the optional Cloud Run path.
- [`.github/docs.yml`](.github/docs.yml) builds the MkDocs site for doc-surface regression checks.

### GitLab CI

- [`.gitlab-ci.yml`](.gitlab-ci.yml) and [`.gitlab-ci/`](.gitlab-ci/) remain available for GitLab-driven pipelines.

---

## Configuration Reference

All settings are environment-driven. No values should be hardcoded.

### Vector Store

| Variable | Default | Description |
|----------|---------|-------------|
| `CEREBRO_VECTOR_STORE_PROVIDER` | `chroma` | Provider alias |
| `CEREBRO_VECTOR_STORE_URL` | — | DSN for pgvector |
| `CEREBRO_VECTOR_STORE_NAMESPACE` | — | Default namespace |
| `CEREBRO_VECTOR_STORE_COLLECTION_NAME` | `cerebro_documents` | Collection / table name |
| `CEREBRO_VECTOR_STORE_EMBEDDING_DIMENSIONS` | — | Required for pgvector index |
| `CEREBRO_VECTOR_STORE_INDEX_TYPE` | `hnsw` | `hnsw`, `ivfflat`, or `none` |

### Azure AI Search

| Variable | Description |
|----------|-------------|
| `AZURE_SEARCH_ENDPOINT` | `https://<name>.search.windows.net` |
| `AZURE_SEARCH_SERVICE_NAME` | Alternative to endpoint — name is used to derive URL |
| `AZURE_SEARCH_API_KEY` | Admin or query key |
| `AZURE_SEARCH_INDEX_NAME` | Index name (default: `cerebro-documents`) |

### LLM

| Variable | Default | Description |
|----------|---------|-------------|
| `CEREBRO_LLM_PROVIDER` | `llamacpp` | Provider alias |
| `AZURE_OPENAI_ENDPOINT` | — | Azure OpenAI service URL |
| `AZURE_OPENAI_API_KEY` | — | Azure OpenAI key |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | `gpt-4o` | Chat model deployment |
| `AZURE_OPENAI_EMBED_DEPLOYMENT` | `text-embedding-3-small` | Embeddings deployment |
| `ANTHROPIC_API_KEY` | — | Anthropic key |
| `GOOGLE_API_KEY` | — | Gemini key |
| `GROQ_API_KEY` | — | Groq key |

### GCP

| Variable | Description |
|----------|-------------|
| `GCP_PROJECT_ID` | GCP project (never hardcode) |
| `DATA_STORE_ID` | Vertex AI Search data store (never hardcode) |

### Runtime

| Variable | Default | Description |
|----------|---------|-------------|
| `NATS_URL` | `nats://localhost:4222` | NATS JetStream URL |
| `CEREBRO_RERANKER_URL` | `http://localhost:8090` | cerebro-reranker endpoint |

---

## Companion Service: cerebro-reranker

Repo: `~/master/cerebro-reranker`

A dedicated reranking microservice using a HybridEngine pipeline:

```
MiniLM (fast pass) → Electra (precision) → DeBERTa (final score)
```

API: `POST /v1/rerank` — used by `CerebroRerankerClient` in `src/cerebro/core/rerank_client.py`.

GCP Vertex AI reranking is the fallback when the service is unavailable.

---

## Developer Guidelines

1. **Always use Nix.** Enter the shell with `nix develop` before any command. Never `pip install` globally.
2. **Interface first.** Any new LLM or vector store provider must implement the abstract interface in `src/cerebro/interfaces/` and register itself in the corresponding factory (`llm_factory.py` or `vector_store_factory.py`).
3. **No hardcoded IDs.** GCP project IDs, data store IDs, Azure resource names — always via environment variables.
4. **English only.** All user-facing strings, CLI output, TUI labels, and docstrings must be in English.
5. **API endpoints go in `src/cerebro/api/server.py`.** The `dashboard_server.py` file is a legacy stub — do not extend it.
6. **Secrets via SOPS.** Never commit plaintext secrets. Use `sops`-encrypted files and the `age` key.

---

<div align="center">
<sub>Built by VoidNxLabs · Enterprise-grade · Hermetically sealed · Production-ready</sub>
</div>
