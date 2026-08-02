# Command: `cerebro rag backend health`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `rag backend` |
| Command | `health` |
| Function | `rag_backend_health` |
| Source | `src/cerebro/cli.py:769` |
| Syntax | `cerebro rag backend health [--format <output_format>]` |

## 1. Description
Report whether the active RAG backend is healthy.

**Syntax:**
```bash
cerebro rag backend health [--format <output_format>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `output_format` | `option` | `str` | `no` | `table` | `--format` | Output format: table or json |

## 3. Examples
```bash
cerebro rag backend health
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `rag_backend_health`
* Line: `769`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
