# Cerebro Architecture

**Version:** 2.0
**Scope:** Current repository structure under `src/cerebro/`
**Positioning:** Standalone, local-first, integration-friendly

---

## 1. Overview

Cerebro is a repository intelligence and RAG platform centered on a local-first
core. It provides:

- static analysis and repository metrics
- a pluggable RAG engine
- terminal and web interfaces
- optional vendor-specific integrations

The current repository already contains provider contracts that separate the core
application from specific model and vector backends. This is the main mechanism
that enables cloud-agnostic positioning without rewriting the core.

---

## 2. Verified Architectural Boundaries

### 2.1 Provider contracts

The core contracts live in:

- `src/cerebro/interfaces/llm.py`
- `src/cerebro/interfaces/vector_store.py`

These interfaces define the minimum capabilities required by the RAG layer:

- embedding generation
- text generation
- grounded generation with citations
- vector insert/search/delete and health checks

### 2.2 Current provider implementations

The repository currently includes these concrete adapters:

- `src/cerebro/providers/llamacpp/`
- `src/cerebro/providers/openai_compatible/`
- `src/cerebro/providers/chroma/`
- `src/cerebro/providers/gcp/`

This means the design is already integration-friendly, but only one cloud adapter
track is implemented in-tree today: GCP.

### 2.3 RAG engine default behavior

`src/cerebro/core/rag/engine.py` establishes the effective default:

- local LLM by default
- local vector store by default
- optional Vertex AI path when explicitly configured

In practice, the architecture is not cloud-first. The documentation should mirror
that fact.

---

## 3. System Layout

```text
src/cerebro/
  cli.py
  launcher.py
  api/
  commands/
  core/
    extraction/
    rag/
    gcp/
    utils/
  interfaces/
  providers/
    chroma/
    gcp/
    llamacpp/
    openai_compatible/
  intelligence/
  registry/
  tui/
```

### Interface surfaces

- **CLI**: primary operational entrypoint
- **TUI**: Textual-based terminal interface
- **Dashboard/API**: FastAPI-backed HTTP surface plus web frontend

### Core domains

- **Extraction**: analyze repositories and produce structured artifacts
- **RAG**: ingest, retrieve, and generate grounded answers
- **Metrics**: repository scans and health signals
- **Registry/Intelligence**: project discovery and higher-level synthesis

### Optional integration domain

- **GCP**: provider and command modules for Discovery Engine, billing, and related workflows

---

## 4. Local-First Data Flow

The default path can be summarized as:

```text
repository
  -> knowledge analyze
  -> JSONL artifacts
  -> local embeddings via configured LLM provider
  -> Chroma vector store
  -> grounded query with citations
```

This path does not require cloud credentials.

### Ingestion

1. `cerebro knowledge analyze` extracts artifacts into `./data/analyzed/`
2. `cerebro rag ingest` loads those artifacts into the active backend
3. With default configuration, the active backend is local

### Query

1. `cerebro rag query` embeds the question through the configured `LLMProvider`
2. The active `VectorStoreProvider` returns relevant matches
3. The provider generates a grounded answer with citations/snippets

---

## 5. Optional Integration Model

The repository currently ships one cloud integration path: GCP.

This path is implemented across:

- `src/cerebro/providers/gcp/`
- `src/cerebro/core/gcp/`
- `src/cerebro/commands/gcp.py`

These modules are optional from a product perspective. They expand Cerebro with:

- Vertex AI-backed language model workflows
- Discovery Engine search/import flows
- billing and operational utilities

### Design rule

Cloud-specific code belongs in adapters and integration commands, not in the core
contracts or default runtime assumptions.

### Practical consequence

Future vendors should follow the same shape:

- provider implementation under `src/cerebro/providers/<vendor>/`
- optional operational helpers under a vendor-specific integration module
- no vendor lock-in introduced into `interfaces/` or default CLI behavior

---

## 6. Current Command Topology

The CLI groups map to current product boundaries:

- `knowledge`: repository analysis and artifact generation
- `rag`: ingestion, query, rerank
- `metrics`: scans and repository health
- `ops`: operational checks
- `strategy`, `content`, `test`: specialized workflows
- `gcp`: optional vendor-specific integration commands

`gcp` exists as an integration group, but it should not define the public identity
of the product.

---

## 7. Documentation Rules for This Repository

To keep the docs aligned with the code:

1. Describe Cerebro as standalone and local-first.
2. Mention cloud support only as optional and vendor-specific.
3. Avoid claiming multi-cloud implementation unless more than one cloud adapter
   exists in-tree.
4. Reference `src/cerebro/`, not legacy `phantom` paths, when describing the live codebase.
5. Prefer Nix-first execution examples such as `nix develop --command ...`.

---

## 8. Recommended Direction

The repository is already close to the desired posture:

- the core contracts are vendor-agnostic
- the default runtime is local-first
- optional integrations exist behind adapters

The remaining work is mostly coherence work:

- documentation
- packaging and shell defaults
- CI/CD assumptions
- legacy naming cleanup

That makes the current sprint a documentation and boundary-alignment sprint, not a
full architectural rewrite.
