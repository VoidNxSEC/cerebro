# Command: `cerebro knowledge etl`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `knowledge` |
| Command | `etl` |
| Function | `etl_docs` |
| Source | `src/cerebro/cli.py:394` |
| Syntax | `cerebro knowledge etl <source> <destination> [--format <format>]` |

## 1. Description
ETL pipeline for documentation processing.

Extracts, transforms, and loads documentation from various sources
into structured format for indexing.

Example:
    cerebro knowledge etl https://docs.example.com ./data/docs

Migrated from: scripts/etl_docs.py

**Syntax:**
```bash
cerebro knowledge etl <source> <destination> [--format <format>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `source` | `argument` | `str` | `yes` | `Required` | `-` | Documentation source (URL or path) |
| `destination` | `argument` | `str` | `yes` | `Required` | `-` | ETL destination path |
| `format` | `option` | `str` | `no` | `json` | `--format` | Output format: json, jsonl, markdown |

## 3. Examples
```bash
cerebro knowledge etl https://docs.example.com ./data/docs
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `etl_docs`
* Line: `394`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
