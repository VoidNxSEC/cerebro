# Command: `cerebro rag migrate`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `rag` |
| Command | `migrate` |
| Function | `rag_migrate` |
| Source | `src/cerebro/cli.py:573` |
| Syntax | `cerebro rag migrate [--from-provider <from_provider>] [--from-collection <from_collection>] [--from-namespace <from_namespace>] [--from-persist-directory <from_persist_directory>] [--from-url <from_url>] [--from-schema <from_schema>] [--batch-size <batch_size>] [--clear-destination <clear_destination>] [--format <output_format>]` |

## 1. Description
Migrate stored vectors from a source backend into the active RAG backend.

**Syntax:**
```bash
cerebro rag migrate [--from-provider <from_provider>] [--from-collection <from_collection>] [--from-namespace <from_namespace>] [--from-persist-directory <from_persist_directory>] [--from-url <from_url>] [--from-schema <from_schema>] [--batch-size <batch_size>] [--clear-destination <clear_destination>] [--format <output_format>]
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| `from_provider` | `option` | `str` | `no` | `chroma` | `--from-provider` | Source vector store backend |
| `from_collection` | `option` | `str | None` | `no` | `None` | `--from-collection` | Source collection/table name |
| `from_namespace` | `option` | `str | None` | `no` | `None` | `--from-namespace` | Source namespace override |
| `from_persist_directory` | `option` | `str | None` | `no` | `None` | `--from-persist-directory` | Source local persistence path for embedded backends |
| `from_url` | `option` | `str | None` | `no` | `None` | `--from-url` | Source DSN/URL for remote backends |
| `from_schema` | `option` | `str | None` | `no` | `None` | `--from-schema` | Source SQL schema for pgvector |
| `batch_size` | `option` | `int` | `no` | `200` | `--batch-size` | Documents per migration batch |
| `clear_destination` | `option` | `bool` | `no` | `False` | `--clear-destination` | Clear the active destination namespace before copying data |
| `output_format` | `option` | `str` | `no` | `table` | `--format` | Output format: table or json |

## 3. Examples
```bash
cerebro rag migrate
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `rag_migrate`
* Line: `573`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
