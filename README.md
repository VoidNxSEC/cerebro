# Cerebro

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Nix](https://img.shields.io/badge/Nix-Reproducible-5277C3?style=for-the-badge&logo=nixos&logoColor=white)](https://nixos.org/)
[![Tests](https://img.shields.io/badge/Tests-pytest-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](#testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**Cerebro** is a standalone, local-first knowledge and repository intelligence platform.
It combines static analysis, local RAG workflows, terminal and web interfaces, and optional
vendor-specific integrations. The core runtime is designed to work without cloud credentials.

---

## Quick Start

```bash
git clone https://github.com/marcosfpina/cerebro.git
cd cerebro

# Enter the hermetic dev shell
nix develop

# Inspect the environment
cerebro info
cerebro version

# Analyze a repository and build a local RAG index
cerebro knowledge analyze . "General Review"
cerebro rag ingest ./data/analyzed/all_artifacts.jsonl
cerebro rag query "What are the main modules in this repository?"
```

Prefer `nix develop --command ...` for one-shot execution outside an interactive shell.

---

## Product Direction

Cerebro follows three design rules:

- **Standalone first**: code analysis, repository metrics, local retrieval, and core UX do not require cloud access.
- **Cloud optional**: vendor integrations are adapters, not prerequisites.
- **Vendor-specific by implementation**: the architecture is integration-friendly, but the core does not assume a preferred cloud.

The codebase already exposes provider interfaces for language models and vector stores, which
makes local and cloud-backed implementations swappable without changing the application core.

---

## Architecture

```text
                         +---------------------------+
                         |         Cerebro           |
                         |   CLI | TUI | Dashboard   |
                         +-------------+-------------+
                                       |
                         +-------------v-------------+
                         |        Core Services      |
                         | analysis | metrics | rag  |
                         +------+------+-------------+
                                |      |
                +---------------+      +------------------+
                |                                      |
        +-------v--------+                    +--------v---------+
        | Local Providers |                    | Optional Adapters |
        | llama.cpp       |                    | GCP integration   |
        | OpenAI-like API |                    | vendor-specific   |
        | Chroma vector   |                    | commands/providers|
        +-----------------+                    +-------------------+
```

### Current Implementation Status

| Area | Default path | Optional path | Notes |
| --- | --- | --- | --- |
| Code analysis | Tree-Sitter + Python AST | - | Local |
| Repository metrics | Filesystem + git scan | - | Local |
| LLM provider | `llama.cpp` / OpenAI-compatible | Vertex AI adapter | Adapter-based |
| Vector store | ChromaDB | - | Interface already exists |
| RAG ingestion/query | Local-first | GCP-backed workflows | Local remains primary path |
| Interfaces | CLI, TUI, Dashboard | - | Shared core |

---

## Interfaces

### CLI

The Typer CLI is the primary operational surface:

```text
cerebro knowledge   analyze | batch-analyze | summarize | generate-queries | index-repo
cerebro rag         ingest | query | rerank
cerebro metrics     scan | watch | report | compare | check
cerebro ops         health | status
cerebro strategy    optimize | salary | moat | trends
cerebro content     mine | analyze
cerebro test        grounded-search | grounded-gen | verify-api
cerebro gcp         burn | monitor | create-engine | status   # optional integration
```

### TUI

```bash
nix develop --command cerebro tui
```

The Textual interface exposes dashboards, project views, intelligence panels, and operator flows.

### Dashboard

```bash
nix develop --command cerebro dashboard
```

The web dashboard is backed by the FastAPI server in `src/cerebro/api/server.py`, while the
frontend lives under `dashboard/`.

---

## Core Capabilities

### Static Analysis

Analyze repositories using Tree-Sitter and Python AST:

- Python
- JavaScript / TypeScript
- Rust
- Go
- C / C++
- Nix
- Bash

### Repository Intelligence

Collect zero-token operational and structural metrics:

```bash
nix develop --command cerebro metrics scan
nix develop --command cerebro metrics report .
nix develop --command cerebro metrics watch
```

### Local-First RAG

The default RAG path stays local:

- Pluggable `LLMProvider`
- Pluggable `VectorStoreProvider`
- ChromaDB as the current built-in vector store
- `llama.cpp` and OpenAI-compatible endpoints as local-friendly LLM options

### Optional Integrations

The repository currently ships one cloud integration track: GCP.

These commands are optional and integration-specific:

```bash
nix develop .#gcp --command cerebro gcp status
nix develop .#gcp --command cerebro gcp monitor --project <project-id>
nix develop .#gcp --command cerebro gcp burn --project <project-id> --engine <engine-id>
```

This integration exists beside the local core; it does not define the product.

---

## Documentation

All project documentation lives in [`docs/`](docs/).

### Start Here

| Document | Description |
| --- | --- |
| [Documentation Hub](docs/README.md) | Overview and quick navigation |
| [Documentation Index](docs/INDEX.md) | Topic-based navigation |
| [Architecture](docs/architecture/ARCHITECTURE.md) | Current architecture overview |
| [Command Reference](docs/commands/README.md) | CLI command usage |

### Selected Topics

| Area | Documents |
| --- | --- |
| Core product | [Quick Start](docs/guides/QUICK_START.md), [Cheatsheet](docs/guides/CHEATSHEET.md), [Keyboard Shortcuts](docs/guides/KEYBOARD_SHORTCUTS.md) |
| Architecture | [Architecture Overview](docs/architecture/ARCHITECTURE.md), [Data Flow](docs/architecture/ARCHITECTURE_DATA_FLOW.md), [ADR Summary](docs/architecture/ADR_SUMMARY.md) |
| Intelligence | [Capabilities](docs/features/intelligence/CAPABILITIES.md), [Sources](docs/features/intelligence/INTEL_SOURCES.md), [Stack Mastery](docs/features/intelligence/STACK_MASTERY.md) |
| Integration-specific | [GCP Credits](docs/features/gcp-credits/README.md), [Automation Systems](docs/features/gcp-credits/AUTOMATION_SYSTEMS.md) |
| Project planning | [Master Execution Plan](docs/project/MASTER_EXECUTION_PLAN.md), [Status](docs/project/STATUS.md), [Coverage Gaps](docs/project/COVERAGE_GAP.md) |

---

## Testing

```bash
# Core unit test path
nix develop --command pytest tests/ --ignore=tests/integration

# Core smoke path
nix develop --command cerebro ops health

# Optional integration tests
nix develop .#gcp --command pytest tests/integration/ -m integration
```

Some integration tests exercise optional external adapters and may require additional configuration.

---

## Project Structure

```text
src/cerebro/
  cli.py                 CLI entrypoint
  launcher.py            CLI / TUI / dashboard launcher
  api/                   FastAPI services
  commands/              Command groups
  core/
    extraction/          Repository analysis and ingestion
    rag/                 Retrieval and generation engine
    gcp/                 Optional GCP integration utilities
    utils/               Logging, resilience, helpers
  interfaces/            Provider contracts
  providers/
    chroma/              Built-in vector store provider
    llamacpp/            Local llama.cpp adapter
    openai_compatible/   OpenAI-compatible HTTP adapter
    gcp/                 Optional GCP provider adapter
  registry/              Repository discovery and indexing
  intelligence/          Intelligence domain models and workflows
  tui/                   Textual application

dashboard/               Web frontend
docs/                    Documentation
tests/                   Unit and integration tests
config/                  Project configuration
```

---

## Configuration

### Local-first defaults

```bash
export CEREBRO_LLM_PROVIDER="llamacpp"
export LLAMA_CPP_URL="http://localhost:8081"
export LLAMA_CPP_MODEL="current-model"
```

### Optional OpenAI-compatible provider

```bash
export CEREBRO_LLM_PROVIDER="openai-compatible"
export OPENAI_COMPATIBLE_URL="http://localhost:8000"
export OPENAI_COMPATIBLE_MODEL="current-model"
```

### Optional GCP adapter

```bash
export CEREBRO_LLM_PROVIDER="vertex-ai"
export GCP_PROJECT_ID="<your-gcp-project-id>"
export DATA_STORE_ID="<your-data-store-id>"
```

---

## Contributing

1. Use the Nix environment for development and validation.
2. Keep the core product local-first and vendor-agnostic.
3. Treat cloud integrations as optional adapters.
4. Do not hardcode credentials, project IDs, or vendor-specific identifiers.

See [docs/guides/CONTRIBUTING_DOCS.md](docs/guides/CONTRIBUTING_DOCS.md) for the current documentation workflow.

---

## License

MIT License. See [LICENSE](LICENSE).
