# Changelog

All notable changes to Cerebro are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [PEP 440](https://peps.python.org/pep-0440/).

---

## [1.0.0b1] - 2026-04-05

### Added

**Anthropic Claude provider** (`CEREBRO_LLM_PROVIDER=anthropic` or `claude`)
- Default model: `claude-sonnet-4-6`
- Embeddings delegated to local `EmbeddingSystem` (Anthropic has no embeddings API)
- Config: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `ANTHROPIC_TIMEOUT`
- Install: `poetry install --with anthropic`

**Groq provider** (`CEREBRO_LLM_PROVIDER=groq`)
- Default model: `llama-3.3-70b-versatile`
- Embeddings delegated to local `EmbeddingSystem` (Groq has no embeddings API)
- Config: `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_TIMEOUT`
- Install: `poetry install --with groq`

**Gemini provider** (`CEREBRO_LLM_PROVIDER=gemini` or `google-gemini`)
- Default generation model: `gemini-1.5-flash`
- Native embeddings via `google-generativeai` SDK (`models/text-embedding-004`)
- Config: `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_EMBEDDING_MODEL`, `GEMINI_TIMEOUT`
- Install: `poetry install --with gemini`

**Nix packaging**
- `packages.default` in `flake.nix` via `poetry2nix.mkPoetryApplication` — enables `nix build` and `nix run`
- `nix/cerebro.nix` — standalone `buildPythonPackage` derivation for nixpkgs PR submission

**New provider aliases** registered in `RigorousRAGEngine`:

| Alias | Canonical |
|-------|-----------|
| `anthropic` | `anthropic` |
| `claude` | `anthropic` |
| `groq` | `groq` |
| `gemini` | `gemini` |
| `google-gemini` | `gemini` |

### Changed

- **Version bumped** from `0.1.0` to `1.0.0b1` (BETA launch)
- `src/cerebro/__init__.__version__` aligned to `1.0.0b1` (was inconsistently `2.0.0`)
- `.env.example` documents env vars for all three new providers
- `Justfile` gains a `release` recipe and a `todo` progress tracker

---

## [0.1.0] - Initial release

- Local-first RAG engine with llama.cpp + ChromaDB
- OpenAI-compatible provider adapter
- Optional Google Vertex AI integration
- React dashboard + Textual TUI
- GCP credits monitoring (optional)
