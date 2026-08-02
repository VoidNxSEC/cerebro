# Azure AI Search Operational Runbook

**Backend:** `azure_search` (aliases: `azure-search`, `azuresearch`, `cognitive-search`)  
**When to choose:** Fully-managed cloud vector search on Azure, no infrastructure to run,
integrated with Azure RBAC, audit logs, and Microsoft Defender. Best for enterprise Azure
tenants needing a zero-ops vector backend.  
**When NOT to choose:** Air-gapped / offline environments, self-hosted requirements,
or when you need to read back stored embedding vectors (Azure Search does not return
vectors through the search API — see §Export Limitation).

---

## 1. Bootstrap

```bash
# Set required credentials
export CEREBRO_VECTOR_STORE_PROVIDER=azure_search
export AZURE_SEARCH_ENDPOINT="https://<your-service>.search.windows.net"
export AZURE_SEARCH_API_KEY="<your-admin-key>"
export AZURE_SEARCH_INDEX_NAME=cerebro-documents   # or via CEREBRO_VECTOR_STORE_COLLECTION_NAME

# Initialize index (HNSW, idempotent)
cerebro rag backend init
# Creates the index with vectorSearch HNSW profile, OData-filterable fields,
# and SemanticConfiguration if available.
```

Azure portal alternative: Create a new search index with:
- Field `id` (Edm.String, key=true)
- Field `content` (Edm.String, searchable=true)
- Field `embedding` (Collection(Edm.Single), dimensions=384, vectorSearch algorithm)
- Fields `namespace`, `repo`, `source`, `git_commit`, `title` (Edm.String, filterable=true)

---

## 2. Health Check

```bash
cerebro rag backend health
# Calls GET <endpoint>/indexes/<index>?api-version=2024-07-01

# Directly via REST
curl -H "api-key: $AZURE_SEARCH_API_KEY" \
    "$AZURE_SEARCH_ENDPOINT/indexes/cerebro-documents?api-version=2024-07-01"
```

---

## 3. Index Export and Backup

> **Note:** Azure AI Search does not return stored vectors through the search API.
> Backup strategies must account for this limitation.

**Backup approach A — Re-index from source:**
Store source documents (JSONL, GCS, Azure Blob) and re-ingest on rollback.

**Backup approach B — Export document metadata (no vectors):**
```bash
cerebro rag backend migrate --from-provider azure_search --to pgvector
# Migrates content + metadata; vectors are re-embedded at destination
```

**Azure native backup (index definition only):**
```bash
# Export index schema
curl -H "api-key: $AZURE_SEARCH_API_KEY" \
    "$AZURE_SEARCH_ENDPOINT/indexes/cerebro-documents?api-version=2024-07-01" \
    > cerebro_index_schema_$(date +%Y%m%d).json
```

---

## 4. Restore

```bash
# Re-create index from saved schema
curl -X PUT \
    -H "api-key: $AZURE_SEARCH_API_KEY" \
    -H "Content-Type: application/json" \
    "$AZURE_SEARCH_ENDPOINT/indexes/cerebro-documents?api-version=2024-07-01" \
    -d @cerebro_index_schema_20260419.json

# Re-ingest from JSONL source
cerebro rag ingest ./data/analyzed/all_artifacts.jsonl
```

---

## 5. Rollback via Index Alias (Preview)

Azure AI Search supports index aliases starting with API version `2023-10-01-Preview`:
```bash
# Create alias pointing to current index
curl -X PUT \
    -H "api-key: $AZURE_SEARCH_API_KEY" \
    -H "Content-Type: application/json" \
    "$AZURE_SEARCH_ENDPOINT/aliases/cerebro?api-version=2023-10-01-Preview" \
    -d '{"name": "cerebro", "indexes": ["cerebro-documents-v2"]}'

# Rollback: update alias to previous index
curl -X PUT ... -d '{"name": "cerebro", "indexes": ["cerebro-documents-v1"]}'
```

Then set `AZURE_SEARCH_INDEX_NAME=cerebro` (the alias name) for zero-downtime rollback.

---

## 6. Namespace Audit

Azure Search filters on `namespace` via OData:
```bash
# Count documents per namespace
curl -H "api-key: $AZURE_SEARCH_API_KEY" \
    -H "Content-Type: application/json" \
    -X POST \
    "$AZURE_SEARCH_ENDPOINT/indexes/cerebro-documents/docs/search?api-version=2024-07-01" \
    -d '{"search": "*", "facets": ["namespace,count:50"], "top": 0}'
```

---

## 7. Monitoring

| Metric | Location |
|--------|----------|
| Document count | Azure Portal → Search Service → Indexes → cerebro-documents |
| Index size | Portal → Overview → Storage used |
| Query latency | Portal → Metrics → Search Latency (p50, p99) |
| Throttling | Portal → Metrics → Throttled Search Queries Percentage |
| Audit logs | Azure Monitor → Diagnostic settings → `operationName: "Query.Search"` |

Environment variables:
- `AZURE_SEARCH_ENDPOINT` — service endpoint URL
- `AZURE_SEARCH_API_KEY` — admin key (or use `AZURE_CLIENT_ID` + managed identity)
- `AZURE_SEARCH_INDEX_NAME` — index name (default: `cerebro-documents`)
- `CEREBRO_VECTOR_STORE_EMBEDDING_DIMENSIONS` — vector dimensions (default: 384)
- `CEREBRO_VECTOR_STORE_NAMESPACE` — default namespace scope
