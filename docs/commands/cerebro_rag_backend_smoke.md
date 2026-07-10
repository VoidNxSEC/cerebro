# Command: `cerebro rag backend smoke`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `rag backend` |
| Command | `smoke` |
| Function | `rag_backend_smoke` |
| Source | `src/cerebro/cli.py:822` |
| Syntax | `cerebro rag backend smoke [--format <output_format>] [--skip-write-check <skip_write_check>]` |

## 1. Description
Run a smoke test against the active RAG backend.

**Syntax:**
```bash
cerebro rag backend smoke [--format <output_format>] [--skip-write-check <skip_write_check>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `output_format` | `option` | `str` | `no` | `table` | `--format` | Output format: table or json |
| `skip_write_check` | `option` | `bool` | `no` | `False` | `--skip-write-check` | Skip the temporary write/read/delete validation cycle |

## 3. Examples
```bash
cerebro rag backend smoke
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `rag_backend_smoke`
* Line: `822`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
