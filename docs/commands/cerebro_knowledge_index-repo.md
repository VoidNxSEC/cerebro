# Command: `cerebro knowledge index-repo`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `knowledge` |
| Command | `index-repo` |
| Function | `index_repository` |
| Source | `src/cerebro/cli.py:355` |
| Syntax | `cerebro knowledge index-repo [<repo_path>] [--force <force>] [--output <output>]` |

## 1. Description
Index a code repository for knowledge base.

Extracts code structure, documentation, and metadata for indexing.

Example:
    cerebro knowledge index-repo ~/projects/myapp --force

Migrated from: scripts/index_repository.py

**Syntax:**
```bash
cerebro knowledge index-repo [<repo_path>] [--force <force>] [--output <output>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `repo_path` | `argument` | `str` | `no` | `.` | `-` | Repository path to index |
| `force` | `option` | `bool` | `no` | `False` | `--force, -f` | Force re-indexing |
| `output` | `option` | `str | None` | `no` | `None` | `--output` | Output directory |

## 3. Examples
```bash
cerebro knowledge index-repo ~/projects/myapp --force
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `index_repository`
* Line: `355`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
