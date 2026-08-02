# Command: `cerebro rag rerank`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `rag` |
| Command | `rerank` |
| Function | `rag_rerank` |
| Source | `src/cerebro/cli.py:944` |
| Syntax | `cerebro rag rerank <query> [--documents <documents_file>] [--top-k <top_k>]` |

## 1. Description
Rerank documents using a cross‑encoder model (service or local fallback).

**Syntax:**
```bash
cerebro rag rerank <query> [--documents <documents_file>] [--top-k <top_k>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `query` | `argument` | `str` | `yes` | `Required` | `-` | Search query |
| `documents_file` | `option` | `str` | `no` | `./data/analyzed/all_artifacts.jsonl` | `--documents, -d` | JSONL file containing documents |
| `top_k` | `option` | `int` | `no` | `10` | `--top-k, -k` | Number of top results to return |

## 3. Examples
```bash
cerebro rag rerank
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `rag_rerank`
* Line: `944`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
