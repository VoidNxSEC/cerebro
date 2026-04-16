```html
<div align="center">
```

# 🧠 CEREBRO

**Enterprise Knowledge Extraction & Distributed RAG Platform**

[!\[Python 3.13+\](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge\&logo=python\&logoColor=white)](https://www.python.org/)
[!\[Nix Reproducible\](https://img.shields.io/badge/Nix-Reproducible-5277C3?style=for-the-badge\&logo=nixos\&logoColor=white)](https://nixos.org/)
[!\[Azure Ready\](https://img.shields.io/badge/Azure-OpenAI\_Ready-0078D4?style=for-the-badge\&logo=microsoft-azure\&logoColor=white)](https://azure.microsoft.com/)
[!\[Proprietary\](https://img.shields.io/badge/License-Proprietary-red.svg?style=for-the-badge)](#)

```html
</div>
```

---

**Cerebro** is a standalone, hermetic knowledge and repository intelligence platform. It natively combines deep static analysis (ASTs), local RAG workflows, beautiful terminal interfaces (TUI), and production-grade Cloud integration adapters (Azure, GCP).

Built rigidly around **Nix-first** reproducibility, the core runtime ensures that what works on your machine flawlessly scales to your Kubernetes clusters and Enterprise environments.

## ⚡ 1-Minute Quickstart

> \[!TIP]
> The fastest way to start is using the Nix hermetic shell. No virtual environments. No hidden global packages.

```bash
# 1. Enter the highly-styled hermetic development environment
nix develop

# 2. Run the interactive setup to configure your LLM/Azure
cerebro setup

# 3. Analyze code & query your intelligence
cerebro knowledge analyze . "General codebase review"
cerebro rag ingest ./data/analyzed/all_artifacts.jsonl
cerebro rag query "Explain the architecture of the Core Services"
```

## 🏗️ Architecture Design

Cerebro separates concerns aggressively: Local logic runs entirely free of the cloud, but plugging into Enterprise scalability (via Azure or Elasticsearch) is native.

```javascript
graph TD
    %% Styling
    classDef default fill:#1e1e1e,stroke:#4a4a4a,stroke-width:2px,color:#fff;
    classDef highlight fill:#5277c3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef adapter fill:#0078d4,stroke:#fff,stroke-width:2px,color:#fff;

    subgraph "Cerebro Unified Surface"
        CLI("Interactive CLI (Rich)")
        CDASH("React Dashboard (Port: 18321)")
        CTUI("Textual TUI")
    end

    subgraph "Core Intelligence Engine"
        AST["AST Static Analysis (TreeSitter)"]
        Metrics["Repo Metrics (Zero-token)"]
        RAG["Rigorous RAG Engine"]
    end

    subgraph "Pluggable Storage (Vector Stores)"
        Chroma["Local ChromaDB"]
        ES["Elasticsearch (Hybrid RRF)"]
        PG["PGVector"]
    end

    subgraph "Pluggable Compute (LLMs)"
        Llama["Llama.cpp (Local)"]
        Azure["Azure OpenAI (Enterprise)"]:::adapter
        GCP["GCP Vertex AI"]
    end

    %% Flow
    CLI --> AST
    CDASH --> RAG
    CTUI --> Metrics

    AST --> RAG
    Metrics --> RAG

    RAG --> Chroma
    RAG --> ES
    RAG --> PG

    RAG --> Llama
    RAG --> Azure
    RAG --> GCP
```

## 🎮 Intuitive Command Surface

Cerebro is built with Developer Experience (DX) natively in mind. Type `chelp` inside the Nix shell anytime.

| Command Group       | Description                                                           |
| ------------------- | --------------------------------------------------------------------- |
| `cerebro setup`     | Interactive `.env` wizard mapping connection variables naturally.     |
| `cerebro knowledge` | Parse codebases safely, extracting syntax trees and dependencies.     |
| `cerebro rag`       | Query, ingest, and fusion search using Reciprocal Rank Fusion (RRF).  |
| `cerebro ops`       | Execute K8s compatible liveness and readiness health checks.          |
| `cdash` / `ctui`    | Jump straight into the graphical (Browser/Terminal) dashboard arrays. |

> \[!NOTE]
> Detailed commands lie in the`cerebro --help` index.

## 🌩️ Multi-Cloud & Enterprise Ready

### [Azure Setup (Native Adapter)](docs/guides/AZURE.md)

We prioritize **Azure OpenAI** for scaling workloads.
Just configure `CEREBRO_LLM_PROVIDER=azure` via `cerebro setup`, mapping your Entra ID credentials or API tokens natively under the `AzureOpenAIProvider`.

### [Kubernetes Orchestration](kubernetes/README.md)

Find raw, production-grade `.yaml` definitions in `/kubernetes`. Cerebro splits cleanly into backend RAG APIs (port 8000) and analytical dashboards (port 18321). You can spin this via `kubectl apply -k kubernetes/`.

## 🛠️ Internal Setup Guidelines

1. **Always use Nix.** Never `pip install`. If adding packages, wrap them in `flake.nix` inside the `poetry2nix` directives.
2. Architecture requires **Abstract Interfaces**. If introducing AWS or Anthropic, bind them through `src/cerebro/interfaces/llm.py`.

---

```html
<div align="center">
<i>Proprietary internal architecture. Built tightly, hermetically mapped, and highly scalable.</i>
</div>
```
