# Cerebro - Enterprise Knowledge Extraction Platform

## Identity

- **Product name**: Cerebro
- **What it is**: Enterprise Knowledge Extraction Platform — code analysis, RAG, and GCP integration
- **What it is NOT**: A "credit burn" tool. GCP credit management is ONE feature, not the identity

## Naming Convention

| Scope | Name |
|-------|------|
| Product / CLI | **Cerebro** (`cerebro` command) |
| Python package dir | `src/phantom/` (kept for backward compat — do NOT rename) |
| CLI entrypoints | Both `cerebro` and `phantom` work (backward compat) |
| Imports in code | `from phantom.core...` (internal, not user-facing) |

### Why `src/phantom/` still exists

The internal package is `phantom` for historical reasons. The product name is **Cerebro**.
Renaming `src/phantom/` → `src/cerebro/` affects **71 Python files + CI/scripts** and is
**deliberately postponed** until a dedicated migration sprint. Do NOT start a partial rename.

When the rename happens it will be done atomically:
1. `sed -i 's/from phantom\./from cerebro./g'` across all files
2. Update `pyproject.toml` package declaration
3. Update all shell scripts and CI refs in one commit

## Language Rules

- All user-facing strings (CLI output, TUI labels, docstrings) MUST be in **English**
- Internal code comments: English preferred
- No Portuguese in any user-facing surface

## GCP Configuration

- **Never hardcode** GCP project IDs — use `os.getenv("GCP_PROJECT_ID")`
- **Never hardcode** Data Store IDs — use `os.getenv("DATA_STORE_ID")`
- Placeholder in docs/help: `<your-gcp-project-id>`

## Project Structure

```
src/phantom/           # Python package (internal name)
  cli.py               # CLI entrypoint (Typer)
  tui/                 # Terminal UI (Textual)
  core/                # Business logic
  commands/            # CLI command groups
dashboard/             # React web dashboard
docs/
  architecture/        # Architecture docs, ADR summary
  guides/              # Setup guides, cheatsheets
  features/            # Feature-specific docs (gcp-credits, intelligence, strategy)
  project/             # Project status, plans, audits
  phases/              # Historical phase implementation docs
  i18n/                # Portuguese translations
  commands/            # CLI command docs
```

## Companion Services

| Service | Repo | Role |
|---------|------|------|
| **cerebro-reranker** | `~/master/cerebro-reranker` | Primary reranker (HybridEngine: MiniLM → Electra → DeBERTa). API: `POST /v1/rerank`. GCP Vertex Search is the **fallback**. |

Integration point: `src/phantom/core/rerank_client.py` → `CerebroRerankerClient`.
Endpoint: `http://localhost:8000` (env: `CEREBRO_RERANKER_URL`).

## Dashboard Backend

- Launcher (`src/phantom/launcher.py`) starts **`phantom.api.server:app`** on port 8000.
- `src/phantom/dashboard_server.py` is a **legacy stub** — do NOT use or extend it.
- All new dashboard endpoints go in `src/phantom/api/server.py`.

## Key ADRs

- **ADR-0027**: Phantom Phase 1 API (accepted)
- **ADR-0030**: Enterprise Repositioning & Identity Resolution (accepted)
