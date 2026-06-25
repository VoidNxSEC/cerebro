# Docker & Compose Guide

Run the full Cerebro RAG stack with a single command using Docker Compose.

---

## Prerequisites

| Tool | Min version | Install |
|---|---|---|
| Docker | 24+ | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Docker Compose | v2 (plugin) | bundled with Docker Desktop |
| `curl` | any | system package |

Verify:

```bash
docker version
docker compose version
```

---

## Quick Start (default — ChromaDB local)

```bash
# 1. Clone & enter the repo
git clone <repo-url> cerebro && cd cerebro

# 2. Bootstrap (creates .env, builds image, starts services)
bash scripts/bootstrap.sh

# 3. Verify the API is up
curl http://localhost:8000/health
```

The bootstrap script is idempotent — safe to run again after updating.

---

## Manual Steps

### 1. Environment

```bash
cp .env.example .env
# Edit .env and fill in any keys you need (ANTHROPIC_API_KEY, GROQ_API_KEY, etc.)
```

### 2. Build

```bash
docker compose build
# or via Justfile:
just docker-build
```

### 3. Start

```bash
# Default stack (ChromaDB — no external deps)
docker compose up -d

# Follow logs
docker compose logs -f cerebro
```

### 4. Stop

```bash
docker compose down
# Remove volumes too:
docker compose down -v
```

---

## Vector Store Profiles

Cerebro ships optional sidecar services as Docker Compose profiles.
Activate one by passing `--profile <name>` and pointing the provider env var at it.

### Qdrant

```bash
CEREBRO_VECTOR_STORE_PROVIDER=qdrant \
  docker compose --profile qdrant up -d
```

Qdrant dashboard → <http://localhost:6333/dashboard>

### pgvector (PostgreSQL)

```bash
CEREBRO_VECTOR_STORE_PROVIDER=pgvector \
CEREBRO_VECTOR_STORE_URL="postgresql+psycopg://cerebro:cerebro@postgres/cerebro" \
  docker compose --profile pgvector up -d
```

### OpenSearch

```bash
CEREBRO_VECTOR_STORE_PROVIDER=opensearch \
OPENSEARCH_URL=http://opensearch:9200 \
  docker compose --profile opensearch up -d
```

---

## Environment Variables Reference

All variables can be placed in `.env` at the project root.

### Core

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Host port mapped to the Cerebro API |
| `CEREBRO_VECTOR_STORE_PROVIDER` | `chroma` | Vector backend: `chroma`, `qdrant`, `pgvector`, `opensearch`, `azure_search` |
| `CEREBRO_VECTOR_STORE_COLLECTION_NAME` | `cerebro_knowledge` | Collection / index name |
| `CEREBRO_MODEL` | `TheBloke/Mistral-7B-Instruct-v0.2-GPTQ` | HuggingFace model ID for the local LLM |
| `CEREBRO_QUANTIZATION` | `4bit` | Quantization mode: `4bit`, `8bit`, or `none` |

### LLM Providers

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic Claude (provider: `anthropic`) |
| `GROQ_API_KEY` | Groq (provider: `groq`) |
| `GEMINI_API_KEY` | Google Gemini (provider: `gemini`) |
| `OPENAI_COMPATIBLE_BASE_URL` | Any OpenAI-compatible endpoint |
| `OPENAI_API_KEY` | OpenAI / compatible API key |

### Qdrant profile

| Variable | Default |
|---|---|
| `QDRANT_URL` | `http://qdrant:6333` |
| `QDRANT_API_KEY` | *(empty — no auth)* |

### pgvector profile

| Variable | Default |
|---|---|
| `CEREBRO_VECTOR_STORE_URL` | *(empty)* — set to `postgresql+psycopg://user:pass@postgres/db` |
| `POSTGRES_USER` | `cerebro` |
| `POSTGRES_PASSWORD` | `cerebro` |
| `POSTGRES_DB` | `cerebro` |

### OpenSearch profile

| Variable | Default |
|---|---|
| `OPENSEARCH_URL` | `http://opensearch:9200` |
| `OPENSEARCH_USERNAME` | `admin` |
| `OPENSEARCH_PASSWORD` | `admin` |

---

## Justfile Commands

```bash
just docker-build   # docker compose build
just docker-run     # docker run -p 8000:8000 cerebro:latest (no compose)
```

---

## Health Check

The API exposes `/health`:

```bash
curl http://localhost:8000/health
# {"status":"healthy","model_loaded":true,"uptime_seconds":42.1,...}
```

The compose health check polls this endpoint every 30 s; 3 consecutive failures restart the container.

---

## Troubleshooting

### Image build fails on torch / bitsandbytes

These are large GPU-optional packages. If you don't need local-model quantization, set:

```env
CEREBRO_LLM_PROVIDER=anthropic   # or groq, gemini, openai-compatible
```

and the container never loads the local model, so GPU packages are imported lazily.

### `Cannot connect to the Docker daemon`

```bash
sudo systemctl start docker
# or add your user to the docker group:
sudo usermod -aG docker $USER && newgrp docker
```

### Port 8000 already in use

```bash
PORT=9000 docker compose up -d
curl http://localhost:9000/health
```

### Vector DB data is lost after `docker compose down`

Named volumes persist by default. Data is only removed with `-v`:

```bash
docker compose down        # keeps volumes
docker compose down -v     # destroys volumes (destructive)
```
