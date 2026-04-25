# Reranker Operational Runbook

**Service:** `cerebro-reranker`  
**Repo:** `~/master/cerebro-reranker`  
**Port:** `8090` (env: `CEREBRO_RERANKER_URL`)  
**API:** `POST /v1/rerank`  
**Fallback:** local `CrossEncoderReranker` (MiniLM) — automatic, no configuration needed

---

## Architecture

```
cerebro rag query  →  RigorousRAGEngine
                            │
                            ├─ VectorStoreProvider.search()    (retrieve top-K)
                            │
                            └─ CerebroRerankerClient.rerank()
                                    │
                          ┌─────── ▼ ──────────────────────────┐
                          │  cerebro-reranker (port 8090)       │
                          │  HybridEngine:                      │
                          │    MiniLM → Electra → DeBERTa       │
                          └─────────────────────────────────────┘
                                    │  (unreachable?)
                                    ▼
                          local CrossEncoderReranker (MiniLM)
```

The reranker is optional. If the service is down, Cerebro automatically falls
back to the local model. No manual intervention required.

---

## 1. Starting the Service

```bash
cd ~/master/cerebro-reranker

# Development (Nix)
nix develop --command uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload

# Or via the project launcher
nix develop --command python -m app.main

# Production (Docker)
docker run -d --name cerebro-reranker \
  -p 8090:8090 \
  ghcr.io/your-org/cerebro-reranker:latest
```

---

## 2. Health Check

```bash
curl http://localhost:8090/health
# Expected: {"status": "ok", "models": ["minilm", "electra", "deberta"]}
```

From Cerebro:
```bash
python3 -c "
import requests
r = requests.get('http://localhost:8090/health', timeout=2)
print(r.json())
"
```

---

## 3. Manual Rerank Call

```bash
curl -sX POST http://localhost:8090/v1/rerank \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "how does the authentication middleware work?",
    "documents": [
      "The auth middleware validates JWT tokens on each request.",
      "The rate limiter throttles requests per IP address.",
      "Authentication is handled by the auth module using OAuth2."
    ],
    "top_k": 2
  }' | jq .
```

Expected response:
```json
{
  "results": [
    {"document": "The auth middleware validates JWT tokens...", "score": 0.94, "model": "deberta", "confidence": 0.91},
    {"document": "Authentication is handled by the auth module...", "score": 0.87, "model": "deberta", "confidence": 0.84}
  ]
}
```

---

## 4. Configuration

```bash
# Cerebro-side variables
export CEREBRO_RERANKER_URL=http://localhost:8090   # default
export CEREBRO_RERANKER_MODE=service                # service | local | hybrid

# Modes:
#   service  — prefer service, fallback to local on timeout/error (default)
#   local    — always use local CrossEncoderReranker (no network call)
#   hybrid   — reserved for future multi-stage logic
```

Timeout is controlled by `CerebroRerankerClient(timeout=1.0)` — 1 second default.
Increase if the service runs on a remote host:
```python
from cerebro.core.rerank_client import CerebroRerankerClient
client = CerebroRerankerClient(timeout=5.0)
```

---

## 5. Fallback Behavior

When the service is unreachable or returns an error:

1. `CerebroRerankerClient` logs a `WARNING` and switches to local reranker.
2. `CrossEncoderReranker` loads the MiniLM cross-encoder model (lazy init).
3. Results are returned — slower but functionally equivalent.

To verify fallback is working:
```bash
# Stop the service, then run a query
export CEREBRO_RERANKER_URL=http://localhost:9999  # non-existent
cerebro rag query "describe the auth flow"
# Should complete with: "Reranker service unavailable. Falling back to local model."
```

---

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `Connection refused :8090` | Service not started | `cd ~/master/cerebro-reranker && nix develop --command uvicorn app.main:app --port 8090` |
| High latency on first rerank | Model cold start (MiniLM → DeBERTa cascade) | Normal — subsequent calls are fast |
| `score: 0.0` for all documents | Empty document list passed | Check that `VectorStoreProvider.search()` returned results |
| Service returns 500 | Bug in reranker pipeline | Check `~/master/cerebro-reranker` logs; fallback is automatic |
| Memory spike | DeBERTa loaded for complex queries | Expected; reranker uses ~2–3 GB RAM under load |

---

## 7. Running Alongside the Dashboard

To run the full Cerebro stack locally:

```bash
# Terminal 1 — vector store (example: Qdrant)
nix develop .#rag-qdrant --command qdrant

# Terminal 2 — LLM server (llamacpp)
llama-server --model ~/models/qwen3-8b-q4_k_m.gguf --port 8081

# Terminal 3 — reranker
cd ~/master/cerebro-reranker
nix develop --command uvicorn app.main:app --port 8090

# Terminal 4 — Cerebro dashboard
cd ~/master/cerebro
nix develop --command cerebro dashboard
# Dashboard: http://localhost:18321
# API:       http://localhost:8000

# Terminal 5 — CLI (optional)
nix develop --command cerebro rag query "describe the main services"
```

---

## 8. Integration with NATS (future)

The reranker currently uses a synchronous HTTP sidecar pattern. A future
enhancement would publish rerank requests to a NATS subject and consume results
asynchronously, enabling streaming rerank for large retrieved sets.

When NATS integration lands:
- Subject: `cerebro.rerank.request`
- Reply subject: `cerebro.rerank.reply.<request-id>`
- The `CerebroRerankerClient` will detect `CEREBRO_RERANKER_MODE=nats` and use the NATS transport.
