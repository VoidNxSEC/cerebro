# Command: `cerebro knowledge analyze`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `knowledge` |
| Command | `analyze` |
| Function | `analyze` |
| Source | `src/cerebro/cli.py:188` |
| Syntax | `cerebro knowledge analyze <repo_path> [<task_context>] [<config_file>]` |

## 1. Description
Extract AST and generate JSONL.
Usage: cerebro knowledge analyze ./repo "Context"

**Syntax:**
```bash
cerebro knowledge analyze <repo_path> [<task_context>] [<config_file>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `repo_path` | `argument` | `str` | `yes` | `Required` | `-` | - |
| `task_context` | `argument` | `str` | `no` | `General Review` | `-` | - |
| `config_file` | `argument` | `str` | `no` | `./config/repos.yaml` | `-` | - |

## 3. Examples
```bash
cerebro knowledge analyze
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `analyze`
* Line: `188`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
