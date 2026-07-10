# Command: `cerebro knowledge batch-analyze`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `knowledge` |
| Command | `batch-analyze` |
| Function | `batch_analyze` |
| Source | `src/cerebro/cli.py:262` |
| Syntax | `cerebro knowledge batch-analyze [<config_file>]` |

## 1. Description
Process all repositories defined in the configuration file.

**Syntax:**
```bash
cerebro knowledge batch-analyze [<config_file>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `config_file` | `argument` | `str` | `no` | `./config/repos.yaml` | `-` | - |

## 3. Examples
```bash
cerebro knowledge batch-analyze
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `batch_analyze`
* Line: `262`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
