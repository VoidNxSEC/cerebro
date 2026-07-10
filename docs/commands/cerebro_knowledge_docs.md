# Command: `cerebro knowledge docs`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `knowledge` |
| Command | `docs` |
| Function | `generate_docs` |
| Source | `src/cerebro/cli.py:427` |
| Syntax | `cerebro knowledge docs [<project>] [--output <output>] [--format <format>]` |

## 1. Description
Generate project documentation automatically.

Analyzes code and generates comprehensive documentation with
API references, guides, and examples.

Example:
    cerebro knowledge docs ~/projects/myapp -o ./docs

Migrated from: scripts/generate_docs.py

**Syntax:**
```bash
cerebro knowledge docs [<project>] [--output <output>] [--format <format>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `project` | `argument` | `str` | `no` | `.` | `-` | Project path |
| `output` | `option` | `str` | `no` | `docs/` | `--output` | Output directory |
| `format` | `option` | `str` | `no` | `markdown` | `--format` | Documentation format |

## 3. Examples
```bash
cerebro knowledge docs ~/projects/myapp -o ./docs
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `generate_docs`
* Line: `427`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
