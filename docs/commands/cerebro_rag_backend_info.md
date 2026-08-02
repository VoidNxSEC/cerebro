# Command: `cerebro rag backend info`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `rag backend` |
| Command | `info` |
| Function | `rag_backend_info` |
| Source | `src/cerebro/cli.py:759` |
| Syntax | `cerebro rag backend info [--format <output_format>]` |

## 1. Description
Show detailed information for the active RAG backend.

**Syntax:**
```bash
cerebro rag backend info [--format <output_format>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `output_format` | `option` | `str` | `no` | `table` | `--format` | Output format: table or json |

## 3. Examples
```bash
cerebro rag backend info
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `rag_backend_info`
* Line: `759`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
