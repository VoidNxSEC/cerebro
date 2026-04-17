# Command: `cerebro rag status`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `rag` |
| Command | `status` |
| Function | `rag_status` |
| Source | `src/cerebro/cli.py:661` |
| Syntax | `cerebro rag status [--format <output_format>]` |

## 1. Description
Show the configured production RAG runtime status.

**Syntax:**
```bash
cerebro rag status [--format <output_format>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `output_format` | `option` | `str` | `no` | `table` | `--format` | Output format: table or json |

## 3. Examples
```bash
cerebro rag status
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `rag_status`
* Line: `661`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
