# cerebro test

Integration and API verification commands. Useful for confirming your LLM provider and RAG backend are wired correctly.

## Commands

### `cerebro test grounded-search`

Test grounded search against the active RAG backend.

```bash
cerebro test grounded-search "How does the RAG pipeline work?"
```

Returns retrieved documents with relevance scores. Queries that fall below the relevance gate (0.25) will return a `no_context: true` grounded refusal.

---

### `cerebro test grounded-gen`

Test full grounded generation — retrieval + LLM synthesis.

```bash
cerebro test grounded-gen "Explain the authentication flow"
```

Requires a configured LLM provider (`CEREBRO_LLM_PROVIDER`).

---

### `cerebro test verify-api`

Verify connectivity and response from an arbitrary API endpoint.

```bash
cerebro test verify-api --endpoint http://localhost:8000/health
cerebro test verify-api --endpoint http://localhost:8090/v1/rerank --method POST --payload payload.json
```

| Flag | Description |
|------|-------------|
| `--endpoint` | API endpoint URL (required) |
| `--method` | HTTP method (default: `GET`) |
| `--payload` | JSON payload file for POST/PUT |
| `--headers` | Custom headers as JSON string |
| `--expect-status` | Expected HTTP status code (default: 200) |
