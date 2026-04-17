# Command: `cerebro knowledge generate-queries`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `knowledge` |
| Command | `generate-queries` |
| Function | `generate_queries` |
| Source | `src/cerebro/cli.py:317` |
| Syntax | `cerebro knowledge generate-queries <topic> [--count <count>] [--output <output>]` |

## 1. Description
Generate search queries for a topic.

Creates diverse, high-quality queries for testing and knowledge expansion.

Example:
    cerebro knowledge generate-queries "NixOS configuration" -c 100

Migrated from: scripts/generate_queries.py

**Syntax:**
```bash
cerebro knowledge generate-queries <topic> [--count <count>] [--output <output>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `topic` | `argument` | `str` | `yes` | `Required` | `-` | Topic for query generation |
| `count` | `option` | `int` | `no` | `50` | `--count` | Number of queries to generate |
| `output` | `option` | `Path` | `no` | `queries.json` | `--output` | Output file |

## 3. Examples
```bash
cerebro knowledge generate-queries "NixOS configuration" -c 100
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `generate_queries`
* Line: `317`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
