# Cerebro — Command Cheatsheet

## Setup

```bash
# Enter hermetic dev environment
nix develop

# Interactive setup wizard
cerebro setup wizard

# Verify configuration
cerebro ops health
```

---

## RAG Pipeline

```bash
# Ingest a codebase analysis output
cerebro rag ingest ./data/analyzed/all_artifacts.jsonl

# Ingest with a specific backend
cerebro rag ingest ./data/analyzed/all_artifacts.jsonl --backend chroma

# Query the knowledge base
cerebro rag query "Explain the authentication flow"

# Query with a specific backend
cerebro rag query "How does the RAG pipeline work?" --backend qdrant

# List available backends and capabilities
cerebro rag backends list

# Check ingest status
cerebro rag status
```

---

## Knowledge Extraction

```bash
# Analyze a repository
cerebro knowledge analyze /path/to/repo "Initial analysis"

# Batch analyze multiple repos
cerebro knowledge batch-analyze /path/to/repos/

# Summarize analysis output
cerebro knowledge summarize ./data/analyzed/all_artifacts.jsonl
```

---

## Metrics

```bash
# Full zero-token scan across all repos
cerebro metrics scan

# Real-time interactive watcher
cerebro metrics watch

# Detailed report for one repo
cerebro metrics report /path/to/repo

# Compare metrics across repos
cerebro metrics compare /repo-a /repo-b

# Quick check
cerebro metrics check
```

---

## Operations

```bash
# System health check
cerebro ops health

# Ops status
cerebro ops status
```

---

## Testing & Verification

```bash
# Test grounded search (requires LLM provider)
cerebro test grounded-search "your query"

# Test grounded generation
cerebro test grounded-gen "your query"

# Verify API connectivity
cerebro test verify-api
```

---

## Interfaces

```bash
# TUI (default when no args)
cerebro tui

# API server + dashboard
cerebro dashboard
# frontend: http://localhost:18321
# backend:  http://localhost:8009

# CLI
cerebro --help
cerebro rag --help
cerebro knowledge --help
```

---

## GCP Discovery Engine (optional)

```bash
# Requires: GCP_PROJECT_ID and DATA_STORE_ID env vars
export GCP_PROJECT_ID=<your-gcp-project-id>
export DATA_STORE_ID=<your-data-store-id>

cerebro gcp status
cerebro gcp create-engine
cerebro gcp monitor
```

---

## Environment Variables

```bash
# Copy and fill in
cp .env.example .env
$EDITOR .env
```

Key variables:
| Variable | Description |
|----------|-------------|
| `CEREBRO_LLM_PROVIDER` | `anthropic`, `gemini`, `groq`, `azure`, `llamacpp`, `vertex-ai` |
| `CEREBRO_ARCH_PATH` | Root directory for repo discovery (default: `~/master`) |
| `CEREBRO_VECTOR_DB` | Path to vector store (default: `./data/vectors`) |
| `GCP_PROJECT_ID` | GCP project (only for GCP features) |
| `DATA_STORE_ID` | Discovery Engine data store (only for GCP features) |
| `CEREBRO_RERANKER_URL` | Reranker service URL (default: `http://localhost:8090`) |

---

## Nix Shells

```bash
nix develop            # Default dev shell
nix develop .#brev-deploy  # GPU/Kubernetes deploy tools
```

---

## Deploy

```bash
# Build the deployable API image with Nix
nix build .#dockerImage

# Build and run the Dockerfile-based API container locally
docker build -t cerebro:latest .
docker run --rm -p 8000:8000 cerebro:latest
```

See also: `docs/guides/DEPLOYMENT.md`
