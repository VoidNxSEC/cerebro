# RUNBOOK.md — Bootstrap e Startup Local

**Versao:** 2026-06-27
**Publico:** Desenvolvedor local (NixOS/Nix)

---

## Prerequisitos

| Requisito           | Versao minima | Verificar com           |
|--------------------|---------------|-------------------------|
| Nix                | 2.18+         | `nix --version`         |
| Git                | qualquer      | `git --version`         |
| Docker (opcional)  | 24+           | `docker --version`      |
| just               | 1.x           | `just --version`        |

Os seguintes pacotes sao providos automaticamente pelo `nix develop`:
- Python 3.13, Poetry, pytest, ruff, mypy, black
- chromadb, sentence-transformers, fastapi, uvicorn
- textual, tree-sitter, gitpython
- pkgs.nats-server, pkgs.natscli (binarios do servidor NATS)

---

## Sequencia de bootstrap (primeira vez)

### 1. Entrar no ambiente Nix

```sh
cd /home/kernelcore/master/prod/cerebro
nix develop
```

Isso configura PYTHONPATH, variaveis de ambiente padrao, e atalhos de shell (`chelp`, `cdash`, `ctui`).

### 2. Instalar dependencias Python

```sh
poetry install --only main --no-interaction
```

Para rodar testes, adicionar o grupo dev:

```sh
poetry install --no-interaction
```

### 3. Verificar instalacao

```sh
cerebro info
cerebro version
cerebro ops health
```

### 4. Inicializar o backend RAG (ChromaDB local)

```sh
cerebro rag init
```

Cria o diretorio `./data/vector_db` e inicializa a collection `cerebro_documents`.

### 5. Confirmar RAG funcional

```sh
cerebro rag smoke
```

Deve retornar `Healthy: yes` com steps `initialize`, `health`, `count`, `write`, `query`, `cleanup` todos `ok`.

---

## Startup do servidor API (modo dev)

A porta dev e **8009**. Isso e diferente da porta Docker (8000).

```sh
# Mata processo antigo na porta 8009 e sobe com hot-reload
just serve

# Equivalente manual:
uvicorn cerebro.api.server:app --host 0.0.0.0 --port 8009 --reload
```

Verificar saude apos subir:

```sh
curl http://localhost:8009/health
# {"status":"healthy","service":"cerebro-intelligence","timestamp":"..."}
```

**Nota sobre NATS:** O servidor tenta conectar ao NATS no startup. Sem `nats-py` instalado, loga `WARNING: NATS publisher connection failed (non-fatal)` e continua subindo normalmente. O servidor funciona sem NATS.

---

## Workflow RAG local (sem cloud)

### Analisar um repositorio

```sh
cerebro knowledge analyze /caminho/para/repo "Contexto da analise"
# Output: data/analyzed/<nome-repo>/metrics.json + artifacts.json + all_artifacts.jsonl
```

### Ingerir no ChromaDB

```sh
cerebro rag ingest
# Padrao: lê ./data/analyzed/all_artifacts.jsonl
# Embedding: jinaai/jina-embeddings-v2-base-code (fallback: MPNET, MiniLM)
```

### Consultar a base de conhecimento

```sh
cerebro rag query "Qual o padrao de autenticacao usado nos projetos?"

# Com reranking:
cerebro rag query "Como funciona o pipeline de ingestao?" --rerank --top-k 10
```

### Verificar status do backend

```sh
cerebro rag status
cerebro rag backend health
cerebro rag backends list
```

---

## Workflow com LLM cloud

Requer instalar o provider manualmente ate grupos opcionais serem adicionados ao pyproject.toml:

```sh
# Anthropic (Claude)
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
export CEREBRO_LLM_PROVIDER=anthropic

# Groq
pip install groq
export GROQ_API_KEY="gsk_..."
export CEREBRO_LLM_PROVIDER=groq

# Gemini
pip install google-generativeai
export GEMINI_API_KEY="..."
export CEREBRO_LLM_PROVIDER=gemini

# OpenAI-compatible (e.g. vLLM, Ollama, LM Studio)
pip install openai
export OPENAI_COMPATIBLE_BASE_URL="http://localhost:11434/v1"
export CEREBRO_LLM_PROVIDER=openai_compatible
```

Para llamacpp (local, sem extra deps Python):

```sh
# Subir servidor llama.cpp separadamente
llama-server --model /caminho/para/modelo.gguf --port 8081

# Cerebro detecta automaticamente
export CEREBRO_LLM_PROVIDER=llamacpp
cerebro rag query "pergunta"
```

---

## Benchmark local

Requer servidor API rodando (`just serve`) em :8009.

```sh
# Suite completa (~10-20 min)
cerebro benchmark run

# Suite rapida (~2 min)
cerebro benchmark run --quick

# So embedding (sem RAG, sem ingest)
cerebro benchmark run --no-rag --no-ingest

# Salvar em arquivo especifico
cerebro benchmark run --output docs/benchmarks/benchmark-local.json
```

Output: JSON em `docs/benchmarks/` + tabela Markdown appended em `docs/benchmarks/README.md`.

**Nota:** psutil nao esta em pyproject.toml. Se `benchmark run` falhar com ImportError, instalar: `pip install psutil`.

---

## Docker (producao / reproducibilidade)

Porta Docker e **8000** (diferente da porta dev 8009).

```sh
# Build
docker build -t cerebro:latest .

# Subir apenas Cerebro (ChromaDB embedded)
docker-compose up cerebro

# Com pgvector
docker-compose --profile pgvector up

# Com Qdrant
docker-compose --profile qdrant up

# Com OpenSearch
docker-compose --profile opensearch up
```

Variaveis de ambiente do container (ver docker-compose.yml):
- `CEREBRO_VECTOR_STORE_PROVIDER` — padrao: `chroma`
- `CEREBRO_VECTOR_STORE_URL` — para pgvector DSN
- `QDRANT_URL` — padrao: `http://qdrant:6333`
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`

---

## NATS (integração Spectre)

O NATS server esta disponivel no nix shell via `pkgs.nats-server`. O Python client (`nats-py`) precisa ser adicionado ao pyproject.toml primeiro (ver GAPS.md).

Subir NATS local:

```sh
# No nix shell, nats-server esta no PATH
nats-server --jetstream --port 4222 &

# Verificar streams
nats stream ls

# Monitorar eventos de ingestao
nats sub "ingest.file.sanitized.v1"
nats sub "cognition.insight.generated.v1"
```

Variaveis de ambiente para NATS:

```sh
export NATS_URL="nats://localhost:4222"
export NATS_NKEY_SEED=""  # opcional: NKey para autenticacao
```

O Spectre (em ~/master/prod ou ~/master/staging) e responsavel por publicar em `ingest.file.sanitized.v1`. O Cerebro consome e publica em `cognition.insight.generated.v1`.

---

## Testes

```sh
# Unit tests (sem infra externa)
just test-unit
# equivalente: pytest tests/ -v --ignore=tests/integration --cov=src/cerebro

# Smoke test RAG local
just test-rag-local

# Integration tests (requer infra)
CEREBRO_RUN_INTEGRATION=1 just test-rag-pgvector

# Todos os checks
just validate-all
```

---

## Variaveis de ambiente essenciais

| Variavel                          | Padrao              | Descricao                              |
|----------------------------------|---------------------|----------------------------------------|
| `CEREBRO_LLM_PROVIDER`           | `llamacpp`          | Provider LLM ativo                     |
| `CEREBRO_VECTOR_STORE_PROVIDER`  | `chroma`            | Backend de vetores ativo               |
| `CEREBRO_VECTOR_STORE_PERSIST_DIRECTORY` | `./data/vector_db` | Diretorio ChromaDB         |
| `CEREBRO_VECTOR_STORE_COLLECTION_NAME` | `cerebro_documents` | Nome da collection          |
| `CEREBRO_VECTOR_STORE_NAMESPACE` | None                | Namespace de isolamento                |
| `CEREBRO_API_URL`                | `http://localhost:8009` | URL da API para benchmark          |
| `CEREBRO_DATA_DIR`               | `./data`            | Diretorio de dados principal           |
| `CEREBRO_MIN_RELEVANCE_SCORE`    | `0.25`              | Gate de relevancia minima para RAG     |
| `NATS_URL`                       | `nats://localhost:4222` | URL do servidor NATS               |
| `NATS_NKEY_SEED`                 | vazio               | NKey seed para autenticacao NATS       |
| `LLAMA_CPP_URL`                  | `http://localhost:8081` | URL do servidor llama.cpp          |
| `GCP_PROJECT_ID`                 | None                | Projeto GCP (apenas para Vertex/GCS)   |
| `DATA_STORE_ID`                  | None                | Discovery Engine data store (GCP)      |
| `ANTHROPIC_API_KEY`              | None                | API key Anthropic                      |
| `GROQ_API_KEY`                   | None                | API key Groq                           |
| `GEMINI_API_KEY`                 | None                | API key Gemini                         |

---

## Localizacao de diretorios chave

```
cerebro/
├── src/cerebro/         # Codigo fonte principal
│   ├── api/server.py    # FastAPI app (porta 8009/8000)
│   ├── cli.py           # Entrypoint CLI
│   ├── core/rag/        # RAG engine + embeddings
│   ├── providers/       # LLM e vector store providers
│   ├── nats/            # NATS consumer/publisher (requer nats-py)
│   └── settings.py      # Configuracao via env vars
├── tests/               # Unit tests (mocked)
│   └── integration/     # Integration tests (gated)
├── scripts/             # Scripts utilitarios + benchmark.py
├── data/                # Runtime data (gitignored)
│   ├── vector_db/       # ChromaDB persistido
│   └── analyzed/        # Output de knowledge analyze
├── docs/                # Documentacao (esta pasta)
├── flake.nix            # Nix dev shell
├── pyproject.toml       # Dependencias Python (Poetry)
├── Justfile             # Targets de automacao
└── docker-compose.yml   # Servicos Docker
```
