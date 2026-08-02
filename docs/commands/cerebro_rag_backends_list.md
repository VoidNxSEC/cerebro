# Command: `cerebro rag backends list`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `rag backends` |
| Command | `list` |
| Function | `rag_backends_list` |
| Source | `src/cerebro/cli.py:709` |
| Syntax | `cerebro rag backends list [--format <output_format>]` |

## 1. Description
List the vector store backends known by the current CLI build.

**Syntax:**
```bash
cerebro rag backends list [--format <output_format>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `output_format` | `option` | `str` | `no` | `table` | `--format` | Output format: table or json |

## 3. Examples
```bash
cerebro rag backends list
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `rag_backends_list`
* Line: `709`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
