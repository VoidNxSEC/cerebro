# Command: `cerebro rag init`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `rag` |
| Command | `init` |
| Function | `rag_init` |
| Source | `src/cerebro/cli.py:490` |
| Syntax | `cerebro rag init` |

## 1. Description
Initialize backend-specific storage structures for the active RAG backend.

**Syntax:**
```bash
cerebro rag init
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| - | - | - | - | - | - | - |

## 3. Examples
```bash
cerebro rag init
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `rag_init`
* Line: `490`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
