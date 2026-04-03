# Cerebro Agentic GPT Roadmap

**Date:** 2026-04-02
**Status:** Draft - Ready for Execution
**Objective:** Evolve Cerebro from a knowledge extraction and repository intelligence platform into an agentic engineering runtime powered by grounded GPT workflows.

---

## 1. Verified Baseline

The current repository already provides a strong base:

- CLI, TUI, and dashboard surfaces are present.
- Static analysis, metrics, and RAG flows already exist.
- The provider contract for LLM backends already exists in `src/cerebro/interfaces/llm.py`.
- `src/cerebro/core/rag/engine.py` and `src/cerebro/core/rag/orchestrator.py` show that retrieval and orchestration have already started to separate.
- `src/cerebro/intelligence/core.py` still uses keyword matching for intelligence queries.
- `src/cerebro/dashboard_server.py` still exposes stubbed intelligence endpoints.
- `src/cerebro/providers/openai_compatible/llm.py` already supports OpenAI-style APIs, but there is no dedicated official OpenAI provider yet.

This roadmap focuses on turning those partial capabilities into one coherent runtime.

---

## 2. North Star

Target end-state:

1. One unified knowledge pipeline for code, docs, metrics, alerts, and project metadata.
2. One semantic intelligence layer with filters, citations, and incremental indexing.
3. One GPT-native execution layer able to call internal tools safely.
4. One agent runtime that can `ask`, `investigate`, `fix`, and `brief`.
5. One operational surface across CLI, TUI, and dashboard with observability built in.

---

## 3. Nix Dependency Map

Existing building blocks already present in the flake:

- `python313Packages.fastapi`
- `python313Packages.chromadb`
- `python313Packages.pydantic`

Dependencies to add for the roadmap:

- `python313Packages.openai`
- `python313Packages.networkx`

Any runtime validation should continue to use `nix develop --command ...`.

---

## 4. Architecture Target

Planned architecture:

```text
Sources
  -> analysis + metrics + docs + alerts + git activity
  -> unified ingestion pipeline
  -> canonical knowledge store
  -> semantic retrieval + graph intelligence
  -> tool registry
  -> planner / executor / memory
  -> surfaces: CLI / TUI / dashboard / API
```

Core design rules:

- Keep `LLMProvider` as the provider boundary.
- Keep tool invocation typed and auditable.
- Keep GPT responses grounded in retrieved evidence.
- Keep indexing incremental and deterministic.
- Keep the runtime Nix-first and testable without hidden host dependencies.

---

## 5. Phase Roadmap

## Phase 0 - Foundation and Unification

**Goal:** Remove duplication and define the canonical shape of Cerebro knowledge.

### Deliverables

- Define a canonical intelligence document schema shared by:
  - `src/cerebro/core/rag/engine.py`
  - `src/cerebro/core/rag/orchestrator.py`
  - `src/cerebro/intelligence/core.py`
- Normalize document fields such as:
  - `id`
  - `repo`
  - `path`
  - `symbol`
  - `kind`
  - `content`
  - `metadata`
  - `checksum`
  - `indexed_at`
  - `embedding`
- Consolidate ingestion so the same artifact can flow through analysis, intelligence, and RAG without parallel formats.
- Define where source-of-truth data lives under `data/`.

### TODO

- [ ] Create a canonical schema module for knowledge/intelligence records.
- [ ] Refactor ingestion so `RigorousRAGEngine` and intelligence do not normalize documents differently.
- [ ] Add checksums and timestamps for incremental reindex.
- [ ] Document the canonical data model.

### Exit Criteria

- A single document schema is used end-to-end.
- Reindex decisions can be made deterministically from stored metadata.
- The pipeline no longer depends on ad-hoc JSON shapes.

---

## Phase 1 - Semantic Intelligence

**Goal:** Replace keyword-only intelligence with semantic retrieval and real project-aware querying.

### Deliverables

- Replace the current keyword search in `src/cerebro/intelligence/core.py` with embedding-based retrieval.
- Support filters by project, intelligence type, tags, date window, and threat level.
- Persist intelligence embeddings and retrieval metadata.
- Support incremental indexing of changed repositories or files only.

### TODO

- [ ] Add vector-backed query flow to the intelligence module.
- [ ] Preserve compatibility with existing project registration and ecosystem status APIs.
- [ ] Add ranking metadata to each result.
- [ ] Add citation/source previews to intelligence results.
- [ ] Add tests for semantic search, filters, and empty corpus behavior.

### Exit Criteria

- `query_intelligence()` returns semantic results instead of pure substring matches.
- Queries can be constrained by project and type without custom branching in the caller.
- The intelligence store survives restart and can be refreshed incrementally.

### Suggested Validation

```bash
nix develop --command pytest tests/test_intelligence.py
```

---

## Phase 2 - Dashboard Intelligence Integration

**Goal:** Make the dashboard a real operator surface for intelligence, not only metrics.

### Deliverables

- Replace stub endpoints in `src/cerebro/dashboard_server.py`:
  - `/intelligence/stats`
  - `/intelligence/query`
- Add briefing output backed by real intelligence data and citations.
- Expose confidence, source count, and query latency to the frontend.

### TODO

- [ ] Wire dashboard intelligence endpoints to the real backend.
- [ ] Return typed response payloads instead of placeholder objects.
- [ ] Add API tests for intelligence endpoints.
- [ ] Update the dashboard UI to show evidence, confidence, and project filters.

### Exit Criteria

- Dashboard intelligence panels show live backend results.
- Queries from the UI produce source-backed answers.
- API tests cover the non-stub behavior.

### Suggested Validation

```bash
nix develop --command pytest tests/test_dashboard_server.py tests/test_intelligence.py
```

---

## Phase 3 - GPT-Native Provider Layer

**Goal:** Add a first-class official OpenAI provider without removing local or Vertex options.

### Deliverables

- Create `src/cerebro/providers/openai/` as a dedicated provider module.
- Add `python313Packages.openai` to the Nix environment.
- Support:
  - structured outputs
  - streaming
  - tool-calling
  - explicit model configuration
- Keep `src/cerebro/providers/openai_compatible/` as the generic adapter layer.

### TODO

- [ ] Implement an official OpenAI provider that conforms to `LLMProvider`.
- [ ] Define provider selection through config or environment without breaking existing aliases.
- [ ] Add contract tests similar to `tests/test_openai_compatible_provider.py`.
- [ ] Document model and API-key configuration under Nix shell usage.

### Exit Criteria

- Cerebro can run with an official OpenAI backend and with the existing OpenAI-compatible backend.
- Provider selection is explicit and test-covered.
- Structured outputs can be used by higher-level orchestration code.

### Suggested Validation

```bash
nix develop --command pytest tests/test_openai_compatible_provider.py tests/test_rag.py
```

---

## Phase 4 - Tool Registry and Agent Runtime

**Goal:** Turn Cerebro into a tool-using engineering agent instead of a query-only system.

### Deliverables

- Introduce a typed tool registry for internal capabilities such as:
  - analyze repository
  - scan metrics
  - query intelligence
  - retrieve RAG context
  - generate briefing
  - inspect project health
  - list security findings
- Separate agent concerns into:
  - planner
  - executor
  - tool router
  - memory
  - result formatter
- Add execution modes:
  - `ask`
  - `investigate`
  - `fix`
  - `brief`

### TODO

- [ ] Define tool input/output models with Pydantic.
- [ ] Create a registry and execution wrapper with tracing metadata.
- [ ] Add a planner that produces a multi-step plan from a goal.
- [ ] Add an executor that runs tools with guardrails and stores evidence.
- [ ] Add tests for planning, tool selection, and failure handling.

### Exit Criteria

- Cerebro can decompose a high-level request into multiple tool invocations.
- Tool runs are logged with inputs, outputs, timing, and failure state.
- Agent output is evidence-backed rather than free-form only.

---

## Phase 5 - Memory, Graph Intelligence, and Impact Analysis

**Goal:** Give the agent project memory and system-level reasoning beyond retrieval.

### Deliverables

- Add short-term session memory for active investigations.
- Add persistent project memory for important findings, decisions, and recurring alerts.
- Build a graph layer using `python313Packages.networkx` for:
  - repository dependencies
  - symbol relationships
  - file-to-feature lineage
  - blast-radius analysis

### TODO

- [ ] Model graph nodes and edges from existing analysis artifacts.
- [ ] Add graph queries such as "what breaks if this changes?"
- [ ] Store investigation history with evidence links.
- [ ] Surface graph summaries in briefings and dashboard views.

### Exit Criteria

- Cerebro can answer impact-analysis questions using graph context, not just chunk retrieval.
- Investigations can resume with persisted memory.
- Project relationships become queryable and explorable.

---

## Phase 6 - Operator Surfaces and Autonomous Workflows

**Goal:** Make the system operable in real workflows, not just through backend modules.

### Deliverables

- Add TUI screens for agent execution, plan progress, logs, and evidence.
- Add dashboard views for:
  - tool runs
  - active investigations
  - confidence and citations
  - graph relationships
- Add scheduled workflows for:
  - nightly reindex
  - daily ecosystem briefing
  - security drift review
  - repo health triage

### TODO

- [ ] Extend TUI state to represent running plans and completed steps.
- [ ] Add dashboard routes and components for investigations.
- [ ] Define scheduled entry points for autonomous runs.
- [ ] Add notifications or persisted reports for unattended execution.

### Exit Criteria

- The agent can be operated from CLI, TUI, and dashboard.
- Autonomous jobs produce evidence-backed outputs instead of silent background mutations.
- The system exposes enough telemetry to debug failures quickly.

---

## 6. Cross-Cutting Workstreams

These workstreams should advance in parallel with every phase.

### Testing

- [ ] Expand unit coverage for provider, intelligence, and planner layers.
- [ ] Add integration tests for agent flows and dashboard intelligence endpoints.
- [ ] Keep regression coverage for retrieval quality and source attribution.

### Observability

- [ ] Record query latency, cache hit rate, tool success rate, and planner retries.
- [ ] Add health endpoints for provider, vector store, and intelligence state.
- [ ] Emit structured logs for agent execution traces.

### Security

- [ ] Keep secrets out of persisted tool traces.
- [ ] Audit prompt/tool boundaries before enabling autonomous fix flows.
- [ ] Require explicit evidence collection before remediation recommendations.

### Nix and Runtime Discipline

- [ ] Move new runtime dependencies into `flake.nix` first.
- [ ] Avoid relying on ad-hoc Poetry-only installs for core features.
- [ ] Keep validation commands runnable via `nix develop --command`.

---

## 7. Recommended Execution Order

If execution starts immediately, this is the highest-leverage order:

1. Phase 0 - Foundation and Unification
2. Phase 1 - Semantic Intelligence
3. Phase 2 - Dashboard Intelligence Integration
4. Phase 3 - GPT-Native Provider Layer
5. Phase 4 - Tool Registry and Agent Runtime
6. Phase 5 - Memory, Graph Intelligence, and Impact Analysis
7. Phase 6 - Operator Surfaces and Autonomous Workflows

Reasoning:

- Semantic intelligence unlocks better answers everywhere.
- Dashboard integration turns the new capability into something visible and operable.
- The GPT-native provider is most valuable after the knowledge and retrieval path is stable.
- Agent runtime should sit on top of verified tools and evidence.

---

## 8. First Milestone Cut

If we want an aggressive but coherent first milestone, build this slice first:

- Canonical schema
- Incremental indexing metadata
- Semantic intelligence query backend
- Real dashboard intelligence endpoints
- Minimal official OpenAI provider

That milestone would already transform Cerebro from "analysis plus stubs" into "grounded intelligence runtime with GPT expansion path."

---

## 9. Definition of Done

The roadmap can be considered materially complete when:

- Knowledge ingestion is unified.
- Intelligence queries are semantic and source-backed.
- Dashboard intelligence is real and tested.
- An official GPT provider exists beside local and Vertex providers.
- Cerebro can plan and execute multi-step tool workflows.
- Agent state, evidence, and results are visible across all operator surfaces.

