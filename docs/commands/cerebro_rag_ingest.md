# Command: `cerebro rag ingest`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `rag` |
| Command | `ingest` |
| Function | `rag_ingest` |
| Source | `src/cerebro/cli.py:466` |
| Syntax | `cerebro rag ingest [<source_file>]` |

## 1. Description
Ingest artifacts into the active RAG backend.

**Syntax:**
```bash
cerebro rag ingest [<source_file>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `source_file` | `argument` | `str` | `no` | `./data/analyzed/all_artifacts.jsonl` | `-` | - |

## 3. Examples
```bash
cerebro rag ingest
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `rag_ingest`
* Line: `466`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
