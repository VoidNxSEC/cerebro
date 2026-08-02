# Command: `cerebro knowledge summarize`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `knowledge` |
| Command | `summarize` |
| Function | `summarize` |
| Source | `src/cerebro/cli.py:298` |
| Syntax | `cerebro knowledge summarize <repo_name>` |

## 1. Description
No description provided.

**Syntax:**
```bash
cerebro knowledge summarize <repo_name>
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `repo_name` | `argument` | `str` | `yes` | `Required` | `-` | - |

## 3. Examples
```bash
cerebro knowledge summarize
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `summarize`
* Line: `298`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
