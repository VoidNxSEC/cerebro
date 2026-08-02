# LLM Providers Operational Runbook

**Scope:** Configure, switch, and troubleshoot Cerebro's 7 LLM provider backends.  
**Factory:** `cerebro.providers.llm_factory.build_llm_provider()`  
**Selection variable:** `CEREBRO_LLM_PROVIDER`

---

## Provider Reference

| Provider alias | Canonical | Auth required | Embedding support |
|---------------|-----------|--------------|-------------------|
| `llamacpp`, `local` | `llamacpp` | No | Yes (via server) |
| `anthropic`, `claude` | `anthropic` | `ANTHROPIC_API_KEY` | No |
| `gemini`, `google` | `gemini` | `GEMINI_API_KEY` | Yes |
| `groq` | `groq` | `GROQ_API_KEY` | No |
| `azure`, `azure_openai` | `azure` | `AZURE_OPENAI_API_KEY` | Yes |
| `openai`, `openai_compatible` | `openai_compatible` | Optional | Yes |
| `gcp`, `vertex`, `vertexai` | `gcp` | GCP credentials | Yes (Vertex Search) |

---

## 1. llamacpp (local — default)

Self-hosted llama.cpp server. No API key required.

```bash
export CEREBRO_LLM_PROVIDER=llamacpp
export LLAMA_CPP_URL=http://localhost:8081          # default
export LLAMA_CPP_MODEL=local                        # model name sent in requests
export LLAMA_CPP_TIMEOUT=600                        # seconds
```

Start llama.cpp server (example — Qwen3):
```bash
llama-server \
  --model ~/models/qwen3-8b-q4_k_m.gguf \
  --port 8081 \
  --ctx-size 32768 \
  --n-gpu-layers 99
```

Reasoning model note (Qwen3, DeepSeek-R1): the server returns the answer in
`reasoning_content`, not `content`. The llamacpp provider handles this
transparently via `_extract_content()`.

Health check:
```bash
curl http://localhost:8081/health
```

---

## 2. Anthropic / Claude

```bash
export CEREBRO_LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
export ANTHROPIC_MODEL=claude-sonnet-4-6            # default
export ANTHROPIC_TIMEOUT=120
```

Supported models: `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`

No embedding support — pair with a vector store that has its own embedding pipeline
(e.g., llamacpp for embeddings, Anthropic for generation).

Test call:
```bash
nix develop --command python3 -c "
from cerebro.providers.anthropic.llm import AnthropicProvider
p = AnthropicProvider()
print(p.generate('Say hello in one sentence.'))
"
```

---

## 3. Gemini / Google AI

Requires `google-genai` package (install group `gemini`).

```bash
export CEREBRO_LLM_PROVIDER=gemini
export GEMINI_API_KEY=AIzaSy...
export GEMINI_MODEL=gemini-1.5-flash                # default
export GEMINI_EMBEDDING_MODEL=models/text-embedding-004
export GEMINI_TIMEOUT=120
```

Supported generation models: `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-1.5-flash`  
Embedding task type: `RETRIEVAL_DOCUMENT` (ingestion) / `RETRIEVAL_QUERY` (search)

Install optional group:
```bash
nix develop --command poetry install --with gemini
```

Test:
```bash
nix develop --command python3 -c "
from cerebro.providers.gemini.llm import GeminiProvider
p = GeminiProvider()
print(p.generate('What is RAG in one sentence?'))
"
```

---

## 4. Groq (cloud inference — fast)

```bash
export CEREBRO_LLM_PROVIDER=groq
export GROQ_API_KEY=gsk_...
export GROQ_MODEL=llama-3.3-70b-versatile           # default
export GROQ_TIMEOUT=120
```

Supported models: `llama-3.3-70b-versatile`, `mixtral-8x7b-32768`, `gemma2-9b-it`  
No embedding support.

Rate limits: Groq applies per-model RPM/RPD limits. Monitor via Groq console.

---

## 5. Azure OpenAI

```bash
export CEREBRO_LLM_PROVIDER=azure
export AZURE_OPENAI_API_KEY=...
export AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
export OPENAI_API_VERSION=2024-12-01-preview
export AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o          # default
export AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-ada-002
```

Install optional group:
```bash
nix develop --command poetry install --with azure
```

Deployment names must match your Azure OpenAI resource deployments exactly.

---

## 6. OpenAI-Compatible (generic)

Use for any server exposing the OpenAI `/v1/chat/completions` and
`/v1/embeddings` endpoints: vLLM, LM Studio, Ollama, OpenRouter, etc.

```bash
export CEREBRO_LLM_PROVIDER=openai_compatible
export OPENAI_COMPATIBLE_URL=http://localhost:11434/v1   # Ollama default
export OPENAI_COMPATIBLE_MODEL=qwen3:8b
export OPENAI_COMPATIBLE_API_KEY=                        # empty for local
export OPENAI_COMPATIBLE_TIMEOUT=600
```

For OpenRouter:
```bash
export OPENAI_COMPATIBLE_URL=https://openrouter.ai/api/v1
export OPENAI_COMPATIBLE_API_KEY=sk-or-...
export OPENAI_COMPATIBLE_MODEL=anthropic/claude-3.5-sonnet
```

---

## 7. GCP / Vertex AI

Uses Google Cloud credentials. Requires `GCP_PROJECT_ID` and optionally a
Vertex AI Search data store.

```bash
export CEREBRO_LLM_PROVIDER=gcp
export GCP_PROJECT_ID=<your-gcp-project-id>
export DATA_STORE_ID=<your-data-store-id>          # optional — Vertex Search
```

Authentication:
```bash
gcloud auth application-default login
# or set GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa-key.json
```

---

## Switching Providers at Runtime

```bash
# Switch without restarting (new session picks up env)
export CEREBRO_LLM_PROVIDER=groq
export GROQ_API_KEY=gsk_...
cerebro rag query "what is the auth flow?"

# Verify active provider
cerebro info
```

The settings cache is per-process. Restart any running dashboard server or CLI
session after changing `CEREBRO_LLM_PROVIDER`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `ANTHROPIC_API_KEY is required` | Key not set | `export ANTHROPIC_API_KEY=sk-ant-...` |
| `ModuleNotFoundError: google.genai` | Optional group missing | `poetry install --with gemini` |
| llamacpp returning empty content | Reasoning model (Qwen3/R1) | Provider handles this — verify `LLAMA_CPP_URL` is live |
| Azure `DeploymentNotFound` | Wrong deployment name | Match `AZURE_OPENAI_CHAT_DEPLOYMENT` to Azure portal |
| Groq `rate_limit_exceeded` | RPM cap hit | Back off or switch model |
| Vertex `google.api_core.exceptions.Unauthenticated` | No GCP creds | Run `gcloud auth application-default login` |

---

## Environment Variable Summary

| Variable | Provider | Required | Default |
|----------|---------|---------|---------|
| `CEREBRO_LLM_PROVIDER` | all | No | `llamacpp` |
| `LLAMA_CPP_URL` | llamacpp | No | `http://localhost:8081` |
| `LLAMA_CPP_MODEL` | llamacpp | No | `local` |
| `LLAMA_CPP_TIMEOUT` | llamacpp | No | `600` |
| `ANTHROPIC_API_KEY` | anthropic | **Yes** | — |
| `ANTHROPIC_MODEL` | anthropic | No | `claude-sonnet-4-6` |
| `GEMINI_API_KEY` | gemini | **Yes** | — |
| `GEMINI_MODEL` | gemini | No | `gemini-1.5-flash` |
| `GEMINI_EMBEDDING_MODEL` | gemini | No | `models/text-embedding-004` |
| `GROQ_API_KEY` | groq | **Yes** | — |
| `GROQ_MODEL` | groq | No | `llama-3.3-70b-versatile` |
| `AZURE_OPENAI_API_KEY` | azure | **Yes** | — |
| `AZURE_OPENAI_ENDPOINT` | azure | **Yes** | — |
| `OPENAI_API_VERSION` | azure | No | `2024-12-01-preview` |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | azure | No | `gpt-4o` |
| `AZURE_OPENAI_EMBED_DEPLOYMENT` | azure | No | `text-embedding-ada-002` |
| `OPENAI_COMPATIBLE_URL` | openai_compatible | No | `http://localhost:8081` |
| `OPENAI_COMPATIBLE_MODEL` | openai_compatible | No | `local` |
| `OPENAI_COMPATIBLE_API_KEY` | openai_compatible | No | — |
| `GCP_PROJECT_ID` | gcp | **Yes** | — |
| `DATA_STORE_ID` | gcp | No | — |
