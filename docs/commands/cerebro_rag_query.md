# Command: `cerebro rag query`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `rag` |
| Command | `query` |
| Function | `rag_query` |
| Source | `src/cerebro/cli.py:876` |
| Syntax | `cerebro rag query <question> [--rerank <rerank>] [--top-k <top_k>]` |

## 1. Description
Query the active RAG backend with grounded generation.

**Syntax:**
```bash
cerebro rag query <question> [--rerank <rerank>] [--top-k <top_k>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `question` | `argument` | `str` | `yes` | `Required` | `-` | - |
| `rerank` | `option` | `bool` | `no` | `False` | `--rerank, -r` | Rerank citations with cross‑encoder for better relevance |
| `top_k` | `option` | `int` | `no` | `5` | `--top-k, -k` | Number of results to retrieve |

## 3. Examples
```bash
cerebro rag query
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `rag_query`
* Line: `876`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
