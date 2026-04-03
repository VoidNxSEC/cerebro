# Cerebro

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Nix](https://img.shields.io/badge/Nix-Reproducible-5277C3?style=for-the-badge&logo=nixos&logoColor=white)](https://nixos.org/)
[![Google Cloud](https://img.shields.io/badge/GCP-Vertex_AI-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/vertex-ai)
[![Tests](https://img.shields.io/badge/Tests-112_passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](#testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**Enterprise Knowledge Extraction Platform** — static analysis, RAG pipelines, repository intelligence, and GCP integration. 61 modules, 3 interfaces, 112 tests. Built on Nix for reproducibility, and shipped to linux/MacOS. See the doc for instructions:< >

---

## Quick Start

```bash
git clone https://github.com/marcosfpina/cerebro.git && cd cerebro

# Enter hermetic dev environment (all dependencies resolved automatically)
nix develop

# Verify
cerebro info
cerebro version          # → Cerebro CLI v2.0.0
```

No Nix? Use `poetry install && poetry shell && cerebro info`.

---

## What Cerebro Does

```bash
# 1. Analyze any codebase — extract functions, classes, security issues (zero cloud cost)
cerebro knowledge analyze ./your-project --format json

# 2. Scan repository health — LOC, languages, dependencies, git activity, security
cerebro metrics scan

# 3. Index into the local vector database for semantic search
cerebro rag ingest ./data/analyzed/all_artifacts.jsonl

# 4. Ask natural-language questions with grounded, cited answers
cerebro rag query "Where is credit card validation handled?"
```

---

## Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │              CEREBRO v2.0.0                  │
                    │     Enterprise Knowledge Extraction          │
                    └──────────────────┬──────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
      ┌───────▼───────┐      ┌────────▼────────┐     ┌────────▼────────┐
      │   CLI (Typer)  │      │   TUI (Textual) │     │ Dashboard (React)│
      │  8 cmd groups  │      │  6 screens + KB  │     │ 17 TSX components│
      │  30+ commands  │      │  shortcuts + live │     │ FastAPI backend  │
      └───────┬───────┘      └────────┬────────┘     └────────┬────────┘
              │                        │                        │
              └────────────────────────┼────────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
 ┌──────▼──────┐             ┌─────────▼─────────┐          ┌───────▼───────┐
 │  Analysis    │             │   RAG Engine       │          │  Intelligence  │
 │  Tree-Sitter │             │   Vertex AI +      │          │  Metrics +     │
 │  AST + Security│           │   ChromaDB + Gemini│          │  Health Scores │
 └──────┬──────┘             └─────────┬─────────┘          └───────┬───────┘
        │                              │                              │
        └──────────────────────────────┼──────────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │         Infrastructure               │
                    │   Nix Flake · GCP · FastAPI · Git    │
                    └─────────────────────────────────────┘
```

### Component Status

| Component              | Local                    | Cloud                      | Status         |
| ---------------------- | ------------------------ | -------------------------- | -------------- |
| **Code Analysis**      | Tree-Sitter + Python AST | —                          | Production     |
| **Repository Metrics** | Git + filesystem scan    | —                          | Production     |
| **Vector Store**       | ChromaDB (SQLite)        | Vertex AI Vector Search    | Both supported |
| **LLM Interface**      | llama.cpp / local APIs   | Gemini via Vertex AI       | Both supported |
| **Security Scanner**   | Regex + AST patterns     | —                          | Production     |
| **Dashboard**          | Vite dev server          | —                          | Production     |
| **TUI**                | Textual framework        | —                          | Production     |
| **CI/CD**              | pytest + ruff            | GitLab CI + GitHub Actions | Production     |

---

## Three Interfaces

### CLI

8 command groups, 30+ commands:

```
cerebro knowledge   analyze · batch-analyze · summarize
cerebro rag         ingest · query
cerebro metrics     scan · watch · report
cerebro ops         health · status
cerebro gcp         burn · monitor · create-engine · status
cerebro strategy    optimize · salary · moat · trends
cerebro content     mine · analyze
cerebro test        grounded-search · grounded-gen · verify-api
```

### TUI (Terminal User Interface)

```bash
cerebro tui
```

6 screens: Dashboard, Projects, Intelligence, Scripts, GCP Credits, Logs. Full keyboard navigation (`d` `p` `i` `s` `g` `l` `?` for help). Real-time updates, handles 1000+ projects.

Full shortcut reference: [docs/guides/KEYBOARD_SHORTCUTS.md](docs/guides/KEYBOARD_SHORTCUTS.md)

### Web Dashboard

```bash
cd dashboard && npm install && npm run dev    # → http://localhost:5173
cerebro dashboard                              # Start FastAPI backend
```

React 18 + Vite + TypeScript + TailwindCSS + TanStack Query. Real-time metrics, semantic search, health scores, executive briefings, visual analytics.

Setup: [docs/guides/DASHBOARD_INTEGRATION.md](docs/guides/DASHBOARD_INTEGRATION.md)

---

## Core Capabilities

### Static Analysis

Extract structured artifacts from multiple languages via Tree-Sitter and Python AST:

- **Python** — full AST, imports, docstrings, complexity metrics
- **JavaScript/TypeScript** — Tree-Sitter parsing
- **Rust, Go, C/C++, Nix, Bash** — Tree-Sitter parsing

### Repository Intelligence (Zero-Token)

Scan repositories without any API calls or cloud costs:

```bash
cerebro metrics scan        # Scan all repos: LOC, languages, deps, git, security
cerebro metrics report .    # Detailed report for current repo
cerebro metrics watch       # Real-time file watcher
```

Produces: language distribution, dependency graph, security findings, health scores, git activity metrics, test coverage indicators.

### Enterprise RAG Engine

Production-ready vector search with local-first defaults:

- Automatic batching for local embedding/index flows
- Circuit breakers for rate limits
- Pluggable providers (llama.cpp, OpenAI-compatible local APIs, Vertex AI)
- Grounded generation with citations (hallucination prevention)

### Security Scanner

Built into every analysis pass:

- Secret detection (API keys, passwords, tokens)
- Unsafe code patterns (`eval()`, `exec()`, `pickle.loads()`)
- Dependency auditing (`pyproject.toml`, `package.json`, `Cargo.toml`)
- Per-repository security score (0-100)

### GCP Integration

```bash
cerebro gcp status          # Check SDK + auth
cerebro gcp create-engine   # Provision Discovery Engine
cerebro gcp burn            # Batch queries with cost ceiling
cerebro gcp monitor         # Real-time credit usage
```

---

## Documentation

All documentation lives under [`docs/`](docs/) in structured subdirectories.

### Getting Started

| Document                                                      | Description                                |
| ------------------------------------------------------------- | ------------------------------------------ |
| [Quick Start](docs/guides/QUICK_START.md)                     | Get running in 5 minutes                   |
| [Cheatsheet](docs/guides/CHEATSHEET.md)                       | Daily reference — one-liners and shortcuts |
| [Keyboard Shortcuts](docs/guides/KEYBOARD_SHORTCUTS.md)       | TUI navigation reference                   |
| [Dashboard Integration](docs/guides/DASHBOARD_INTEGRATION.md) | Web dashboard setup                        |

### Architecture

| Document                                                           | Description                             |
| ------------------------------------------------------------------ | --------------------------------------- |
| [Architecture Overview](docs/architecture/ARCHITECTURE.md)         | System design and component interaction |
| [Data Flow Diagram](docs/architecture/ARCHITECTURE_DATA_FLOW.md)   | Pipeline visualization                  |
| [ADR Summary](docs/architecture/ADR_SUMMARY.md)                    | All architectural decisions             |
| [Phoenix Report](docs/architecture/PHOENIX_ARCHITECTURE_REPORT.md) | Migration and restructuring analysis    |

### Features

| Area             | Documents                                                                                                                                                                                                                                         |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Intelligence** | [Capabilities](docs/features/intelligence/CAPABILITIES.md) · [Sources](docs/features/intelligence/INTEL_SOURCES.md) · [Query Mastery](docs/features/intelligence/QUERY_MASTERY.md) · [Stack Mastery](docs/features/intelligence/STACK_MASTERY.md) |
| **GCP Credits**  | [Overview](docs/features/gcp-credits/README.md) · [Automation](docs/features/gcp-credits/AUTOMATION_SYSTEMS.md) · [High-ROI Queries](docs/features/gcp-credits/HIGH_ROI_QUERIES.md)                                                               |
| **Strategy**     | [Executive Summary](docs/features/strategy/EXECUTIVE_SUMMARY.md) · [ROI Analysis](docs/features/strategy/HACKS_ROI.md)                                                                                                                            |

### CLI Commands

Full command reference with examples: [docs/commands/](docs/commands/README.md)

### Project Status

| Document                                                       | Description                     |
| -------------------------------------------------------------- | ------------------------------- |
| [Master Execution Plan](docs/project/MASTER_EXECUTION_PLAN.md) | Active development roadmap      |
| [Status](docs/project/STATUS.md)                               | Current project status          |
| [Coverage Gaps](docs/project/COVERAGE_GAP.md)                  | Known gaps and planned features |
| [Portfolio Audit](docs/project/PORTFOLIO_AUDIT.md)             | Full project audit              |

---

## Roadmap

### Completed (Q4 2025 — Q1 2026)

| Milestone                           | Details                                           | Docs                                                       |
| ----------------------------------- | ------------------------------------------------- | ---------------------------------------------------------- |
| Nix-based reproducible builds       | Flake with poetry2nix, hermetic dev shell         | [Setup Guide](docs/guides/SETUP_COMPLETE.md)               |
| Tree-Sitter polyglot analysis       | Python, JS/TS, Rust, Go, C/C++, Nix, Bash         | [Capabilities](docs/features/intelligence/CAPABILITIES.md) |
| Vertex AI RAG engine                | Batching, circuit breakers, grounded generation   | [Architecture](docs/architecture/ARCHITECTURE.md)          |
| CLI unification (Typer)             | 8 command groups, 30+ commands                    | [Commands](docs/commands/README.md)                        |
| TUI with 6 screens                  | Textual framework, keyboard shortcuts, live data  | [Keyboard Shortcuts](docs/guides/KEYBOARD_SHORTCUTS.md)    |
| React Intelligence Dashboard        | 17 components, FastAPI backend, real-time metrics | [Dashboard Guide](docs/guides/DASHBOARD_INTEGRATION.md)    |
| Zero-token metrics engine           | Repository scanning without API costs             | [Phase 4](docs/phases/PHASE4_COMPLETE.md)                  |
| Enterprise repositioning (ADR-0030) | Rebrand from Phantom to Cerebro                   | [ADR Summary](docs/architecture/ADR_SUMMARY.md)            |
| Production readiness audit          | 112 tests, import fallbacks, i18n cleanup         | [Phase History](docs/phases/)                              |
| GitLab CI/CD pipeline               | Validate, test, build, deploy, monitor stages     | [CI/CD Guide](docs/guides/GITLAB_CI_CD.md)                 |

### In Progress (Q1-Q2 2026)

| Milestone                        | Details                           | Tracking                                                |
| -------------------------------- | --------------------------------- | ------------------------------------------------------- |
| OpenTelemetry observability      | Structured logging, trace context | [Next Steps](docs/project/NEXT_STEPS.md)                |
| REST API + OpenAPI docs          | Public HTTP API for integrations  | [Execution Plan](docs/project/MASTER_EXECUTION_PLAN.md) |
| Terraform infrastructure-as-code | GCP provisioning, Cloud Run       | [Execution Plan](docs/project/MASTER_EXECUTION_PLAN.md) |

### Planned (Q2-Q3 2026)

| Milestone                           | Details                                     | Tracking                                                |
| ----------------------------------- | ------------------------------------------- | ------------------------------------------------------- |
| Vertex AI Vector Search migration   | Replace local ChromaDB for enterprise scale | [Coverage Gaps](docs/project/COVERAGE_GAP.md)           |
| Cloud Run production deployment     | Containerized, auto-scaling                 | [Execution Plan](docs/project/MASTER_EXECUTION_PLAN.md) |
| MCP (Model Context Protocol) server | IDE integration for code intelligence       | [Next Steps](docs/project/NEXT_STEPS.md)                |
| Multi-tenant architecture           | Team/org isolation, RBAC                    | [Execution Plan](docs/project/MASTER_EXECUTION_PLAN.md) |

### Phase History

Full implementation history is tracked in [`docs/phases/`](docs/phases/):

| Phase                         | Document                                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------- |
| Phase 1 — Core extraction     | [Implementation](docs/phases/PHASE1_IMPLEMENTATION.md) · [Validation](docs/phases/PHASE1_VALIDATION.md) |
| Phase 2 — RAG pipeline        | [Complete](docs/phases/PHASE2_COMPLETE.md) · [Roadmap](docs/phases/PHASE2_ROADMAP.md)                   |
| Phase 3 — TUI + commands      | [Complete](docs/phases/PHASE3_IMPLEMENTATION_COMPLETE.md) · [Status](docs/phases/PHASE3_STATUS.md)      |
| Phase 4 — Metrics + dashboard | [Complete](docs/phases/PHASE4_COMPLETE.md) · [Performance](docs/phases/PERFORMANCE_REPORT.md)           |

---

## Testing

```bash
# Full test suite (112 tests)
nix develop --command pytest tests/ --ignore=tests/integration

# With coverage
nix develop --command pytest tests/ --ignore=tests/integration --cov=src/phantom

# Integration tests (requires GCP credentials)
pytest tests/integration/ -m integration

# Quick smoke test
cerebro ops health
```

### Test Coverage

| Module            | Tests | File                              |
| ----------------- | ----- | --------------------------------- |
| CLI commands      | 11    | `tests/test_cli.py`               |
| Code analyzer     | 15    | `tests/test_analyzer.py`          |
| Metrics collector | 28    | `tests/test_metrics_collector.py` |
| Intelligence core | 24    | `tests/test_intelligence.py`      |
| Dashboard server  | 22    | `tests/test_dashboard_server.py`  |
| Launcher          | 9     | `tests/test_launcher.py`          |
| RAG engine        | 6     | `tests/test_rag.py`               |

---

## Project Structure

```
src/phantom/                  # Python package (internal name, kept for backward compat)
  cli.py                      # CLI entrypoint (Typer, 8 command groups)
  launcher.py                 # Auto-detect CLI / TUI / Dashboard
  dashboard_server.py         # FastAPI backend for React dashboard
  tui/                        # Terminal UI (Textual, 6 screens)
  core/
    analyzer.py               # Tree-Sitter + AST code analysis
    metrics_collector.py      # Zero-token repository scanner
    watcher.py                # Real-time file system watcher
    rag/                      # RAG engine + local LLM server
    extraction/               # Code extraction + embeddings
    gcp/                      # GCP service integrations
  intelligence/               # Ecosystem intelligence system
  commands/                   # CLI command group implementations
  interfaces/                 # Provider ABCs (LLM, VectorStore)
  providers/                  # Concrete provider implementations
  registry/                   # Project registry + scanner

dashboard/                    # React web dashboard (Vite + TailwindCSS)
tests/                        # 112 unit tests
docs/
  architecture/               # System design, ADRs
  commands/                   # CLI command reference
  features/                   # Feature docs (intelligence, gcp-credits, strategy)
  guides/                     # Setup, keyboard shortcuts, CI/CD
  phases/                     # Phase implementation history
  project/                    # Status, roadmaps, audits
  i18n/                       # Translations
```

---

## Configuration

### Environment Variables

```bash
# Local-first RAG
export CEREBRO_LLM_PROVIDER="llamacpp"            # default local provider
export LLAMA_CPP_URL="http://localhost:8081"
export LLAMA_CPP_MODEL="current-model"

# Supported aliases:
# llamacpp | llama.cpp | local-llm
# openai-compatible | openai-compatible-api | local-openai
# vertex-ai | vertexai | gcp-vertex-ai

# Optional Vertex AI backend
export GCP_PROJECT_ID="<your-gcp-project-id>"
export DATA_STORE_ID="<your-data-store-id>"

# Cerebro paths
export CEREBRO_ARCH_PATH="$HOME/master/cerebro"    # Repository scan root
export CEREBRO_DATA_DIR="$HOME/master/cerebro/data/intelligence"

# Dashboard
export CEREBRO_CORS_ORIGINS="http://localhost:5173" # Comma-separated origins

# RAG server
export CEREBRO_MODEL="TheBloke/Mistral-7B-Instruct-v0.2-GPTQ"
export CEREBRO_DB="./data/vector_db"

# Reranker Service
export CEREBRO_RERANKER_URL="http://localhost:8090" # Sidecar service URL
export CEREBRO_RERANKER_MODE="service" # service | local | hybrid
export HF_HOME="./data/models" # Cache dir for local fallback models
```

---

## Contributing

1. All changes require passing tests (`nix develop --command pytest tests/ --ignore=tests/integration`)
2. All user-facing strings must be in English (see [CLAUDE.md](CLAUDE.md))
3. Never hardcode GCP project IDs — use `os.getenv("GCP_PROJECT_ID")`
4. Open an issue before starting work on new features

See [Contributing Guide](docs/guides/CONTRIBUTING_DOCS.md) for details.

---

## License

MIT License — see [LICENSE](LICENSE).

---

<p align="center">
  <strong>Cerebro v2.0.0</strong> — 61 Python modules · 22 React components · 112 tests · 14K LoC<br>
  <sub>From local analysis to enterprise production.</sub>
</p>
