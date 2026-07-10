# Command: `cerebro ops health`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `ops` |
| Command | `health` |
| Function | `health` |
| Source | `src/cerebro/cli.py:1007` |
| Syntax | `cerebro ops health` |

## 1. Description
Check system health (Credentials, Permissions, APIs, Data Stores).

**Syntax:**
```bash
cerebro ops health
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| - | - | - | - | - | - | - |

## 3. Examples
```bash
cerebro ops health
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `health`
* Line: `1007`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
