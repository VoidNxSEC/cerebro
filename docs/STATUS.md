# STATUS.md — Cerebro Estado Operacional

**Data da investigação:** 2026-06-27
**Branch:** main
**Ultimo commit:** `9aa5b7e feat(rag): add vertex embeddings and docker compose`

---

## Sumario executivo

Cerebro e uma plataforma de RAG + analise de codigo em estado funcional para o workflow local (ChromaDB + llamacpp). O servidor FastAPI sobe sem erros criticos na porta 8009 (dev) ou 8000 (Docker). O CLI cobre os comandos essenciais com implementacao real. O blocker principal e a ausencia de `nats-py` no `pyproject.toml` — o server tenta conectar ao NATS no startup e falha silenciosamente, tornando o pipeline distribuido inoperante. Providers cloud (anthropic, groq, gemini) tambem nao estao declarados como dependencias opcionais.

---

## Scorecard de saude

| Dimensao               | Score | Notas                                                         |
|------------------------|-------|---------------------------------------------------------------|
| Documentacao           | 5/10  | Muitos .md obsoletos (PHOENIX/GCP credits Jan 2026). Runbook ausente. |
| Testabilidade          | 7/10  | Unit tests com mocks bons. Integration tests gated. tests/tests/ duplicado. |
| Manutenibilidade       | 8/10  | Providers plugaveis, factory pattern, interfaces bem definidas. |
| Divida Tecnica         | 5/10  | 4 TODOs criticos no src/. nats-py faltando. pyproject incompleto. |
| Completude de Features | 7/10  | Core RAG completo. NATS inoperante. Strategy/testing com stubs. |
| Estado de Build/Deploy | 7/10  | Dockerfile OK. docker-compose OK. `nix build .#default` pendente. |
| Momentum               | 8/10  | Commits ativos. Benchmark harness novo. Vertex embeddings recentes. |

---

## Estado por componente

### CLI (`cerebro`)

| Comando                        | Status     | Notas                                                                 |
|-------------------------------|------------|-----------------------------------------------------------------------|
| `cerebro info`                 | FUNCIONAL  | Sem deps externas                                                     |
| `cerebro version`              | FUNCIONAL  | -                                                                     |
| `cerebro ops health`           | FUNCIONAL  | GCP opcional, local OK                                                |
| `cerebro ops status`           | FUNCIONAL  | Lista repos em ./data/analyzed                                        |
| `cerebro knowledge analyze`    | FUNCIONAL  | HermeticAnalyzer + tree-sitter disponivel no nix shell                |
| `cerebro knowledge batch-analyze` | FUNCIONAL | -                                                                  |
| `cerebro knowledge summarize`  | FUNCIONAL  | Requer data/analyzed/<repo>/metrics.json existir                      |
| `cerebro knowledge generate-queries` | PARCIAL | scripts/generate_queries.py e real mas usa templates PT-BR         |
| `cerebro knowledge index-repo` | QUEBRADO   | scripts/index_repository.py hardcoda Discovery Engine (GCP)           |
| `cerebro knowledge etl`        | STUB       | scripts/etl_docs.py importa google-cloud libs                         |
| `cerebro knowledge docs`       | STUB       | scripts/generate_docs.py nao tem implementacao real                   |
| `cerebro rag ingest`           | FUNCIONAL  | ChromaDB local + sentence-transformers                                |
| `cerebro rag query`            | FUNCIONAL  | Requer llamacpp server em :8081 OU outro LLM via env                  |
| `cerebro rag smoke`            | FUNCIONAL  | Testa write/read/delete no backend ativo                              |
| `cerebro rag status`           | FUNCIONAL  | -                                                                     |
| `cerebro rag init`             | FUNCIONAL  | Inicializa schema ChromaDB                                            |
| `cerebro rag migrate`          | FUNCIONAL  | Copia documentos entre backends                                       |
| `cerebro rag rerank`           | FUNCIONAL  | Cross-encoder local (cross-encoder/ms-marco-MiniLM-L-6-v2)           |
| `cerebro rag backends list`    | FUNCIONAL  | Lista chroma/pgvector/qdrant/opensearch/weaviate/azure_search         |
| `cerebro rag backend health`   | FUNCIONAL  | -                                                                     |
| `cerebro benchmark run`        | FUNCIONAL  | scripts/benchmark.py existe e e completo. psutil necessario.          |
| `cerebro strategy optimize`    | STUB       | Tem TODO: "Implement execution logic" no codigo                       |
| `cerebro strategy *`           | PARCIAL    | Outros subcomandos: salary-intel, trend-predict, personal-moat — delegam a scripts GCP |
| `cerebro dashboard`            | CONDICIONAL | Requer React build + launcher. npm + Vite.                           |
| `cerebro tui`                  | FUNCIONAL  | textual disponivel no nix shell via flake.nix                         |
| `cerebro metrics *`            | FUNCIONAL  | MetricsCollector faz scan zero-token dos repos                        |

### LLM Providers

| Provider         | Implementacao | Pacote Python         | Em pyproject.toml | Status                        |
|-----------------|---------------|----------------------|-------------------|-------------------------------|
| llamacpp        | Completa      | stdlib (urllib)      | N/A               | FUNCIONAL (requer server :8081)|
| anthropic       | Completa      | `anthropic`          | NAO               | QUEBRADO (ImportError em runtime)|
| groq            | Completa      | `groq`               | NAO               | QUEBRADO (ImportError em runtime)|
| gemini          | Completa      | `google-generativeai`| NAO               | QUEBRADO (ImportError em runtime)|
| openai_compatible | Completa   | `openai`             | NAO               | QUEBRADO (ImportError em runtime)|
| azure           | Completa      | `langchain-openai`   | grupo azure        | PARCIAL (grupo nao instalado por padrao)|
| vertex_ai       | Completa      | google-cloud packages| grupo gcp          | PARCIAL (requer GCP auth)     |

### Vector Store Backends

| Backend      | Implementacao | Teste Integração  | Requer Infra         | Status                     |
|-------------|---------------|-------------------|----------------------|---------------------------|
| chroma      | Completa      | rag_smoke_test.py | Nenhuma (embedded)   | FUNCIONAL (padrao)        |
| pgvector    | Completa      | test_pgvector*    | PostgreSQL + pgvector| FUNCIONAL (requer DB)     |
| qdrant      | Completa      | test_qdrant*      | Qdrant :6333         | FUNCIONAL (requer server) |
| opensearch  | Completa      | test_opensearch*  | OpenSearch :9200     | FUNCIONAL (requer server) |
| weaviate    | Completa      | test_weaviate*    | Weaviate :8080       | FUNCIONAL (requer server) |
| azure_search| Completa      | test_azure_search*| Azure AI Search      | FUNCIONAL (requer cloud)  |

### API Server (`cerebro.api.server`)

| Endpoint                        | Status     | Notas                                            |
|---------------------------------|------------|--------------------------------------------------|
| `GET /health`                   | FUNCIONAL  | Sempre retorna 200                               |
| `GET /status`                   | FUNCIONAL  | Requer cerebro inicializado                      |
| `GET /projects`                 | FUNCIONAL  | Lista projetos do scanner                        |
| `GET /projects/{name}`          | FUNCIONAL  | Analise por projeto                              |
| `POST /intelligence/query`      | FUNCIONAL  | Keyword + semantic search                        |
| `GET /intelligence/stats`       | FUNCIONAL  | -                                                |
| `POST /briefing`                | FUNCIONAL  | Tipos: daily, executive                          |
| `GET /briefing/daily`           | FUNCIONAL  | -                                                |
| `GET /briefing/executive`       | FUNCIONAL  | -                                                |
| `POST /actions/scan`            | FUNCIONAL  | Scan de projetos em background                   |
| `GET /alerts`                   | FUNCIONAL  | -                                                |
| `GET /graph/dependencies`       | FUNCIONAL  | Grafo de dependencias entre projetos             |
| `GET /rag/status`               | FUNCIONAL  | Estado do RAG backend                            |
| `GET /rag/backends`             | FUNCIONAL  | Lista backends com capacidades                   |
| `GET /ai/health`                | FUNCIONAL  | Verifica llamacpp em :8081                       |
| `POST /chat`                    | FUNCIONAL  | Multi-turn com RAG context. Fallback offline.    |
| `POST /actions/rag/{action}`    | FUNCIONAL  | ingest, smoke, init, migrate                     |
| `POST /actions/knowledge/{action}` | FUNCIONAL | analyze, index                                |
| `POST /actions/ops/health`      | FUNCIONAL  | Health check do sistema                          |
| `GET /metrics`                  | FUNCIONAL  | Snapshot de metricas                             |
| `GET /metrics/watcher`          | FUNCIONAL  | Status do repo watcher                           |
| `POST /metrics/scan`            | FUNCIONAL  | Inicia scan de metricas                          |
| `GET /metrics/{repo}`           | FUNCIONAL  | Metricas por repo                                |
| `POST /actions/summarize/{name}`| FUNCIONAL  | Resumo AI (usa llamacpp se online)               |
| `WebSocket /ws`                 | FUNCIONAL  | Real-time updates, ping/pong, subscribe/unsub    |

### NATS Integration

| Componente         | Arquivo                        | Status       | Blocker                                 |
|-------------------|--------------------------------|--------------|-----------------------------------------|
| Consumer          | src/cerebro/nats/consumer.py   | INCOMPLETO   | `nats` package nao instalado            |
| Publisher         | src/cerebro/nats/publisher.py  | INCOMPLETO   | `nats` package nao instalado            |
| JetStream streams | src/cerebro/nats/streams.py    | INCOMPLETO   | `nats` package nao instalado            |
| Worker            | src/cerebro/nats/worker.py     | INCOMPLETO   | `nats` package nao instalado            |
| Server binaries   | flake.nix (pkgs.nats-server)   | PRESENTE     | Binarios OK, Python client faltando     |

O startup da API (`lifespan`) chama `nats_connect()` que falha silenciosamente com log `WARNING: NATS publisher connection failed (non-fatal)`. O NATS inteiro fica inoperante mas o servidor sobe normalmente.

### Portas em uso

| Servico            | Porta | Contexto                              |
|-------------------|-------|---------------------------------------|
| API server (dev)  | 8009  | `just serve`, server.py `__main__`    |
| API server (docker)| 8000 | docker-entrypoint.sh, docker-compose  |
| LlamaCpp server   | 8081  | llama-server externo                  |
| Dashboard React   | 18321 | Vite dev server                       |
| MkDocs docs       | 8001  | `just docs`                           |

---

## Blockers criticos

1. **`nats-py` ausente do pyproject.toml** — NATS inteiramente inoperante. Server sobe mas pipeline Spectre nao funciona.
2. **Providers cloud sem declaracao em pyproject.toml** — `anthropic`, `groq`, `google-generativeai`, `openai` nao sao instalados por `poetry install --only main`. Qualquer tentativa de usar esses providers resulta em `ImportError` em runtime.
3. **`poetry lock --no-update` pendente** — Justfile TODO. Lock file pode estar desatualizado apos mudancas em pyproject.toml.

---

## Quick wins (alto impacto, baixo esforco)

1. Adicionar `nats-py = "*"` ao `[tool.poetry.dependencies]` em pyproject.toml
2. Criar grupos opcionais em pyproject.toml: `[tool.poetry.group.anthropic.dependencies]`, `groq`, `gemini`, `openai`
3. Adicionar `psutil = "*"` ao pyproject.toml (benchmark --memory falha sem ele)
4. Executar `just test-unit` e documentar quantos passam
5. Executar `just benchmark run --quick` para ter baseline local antes da cloud

---

## Proximas acoes imediatas

1. `poetry add nats-py --lock` — desbloqueia NATS
2. Criar grupos opcionais de providers em pyproject.toml
3. `just test-unit` para verificar cobertura atual
4. `cerebro rag smoke` para confirmar ChromaDB OK
5. `cerebro benchmark run --quick` para baseline local
