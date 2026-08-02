# Weaviate Operational Runbook

**Backend:** `weaviate`  
**When to choose:** Cloud-native, schema-optional vector store with native hybrid search
(BM25 + vector via RRF), multi-tenancy, GraphQL + REST + gRPC APIs.  
Ideal for complex agent pipelines where you need both vector similarity and full-text
recall without managing OpenSearch. Works fully offline with the Nix shell.  
**When NOT to choose:** You need SQL joins on relational metadata, or your team is
exclusively a PostgreSQL shop — pgvector is simpler in that context.

---

## 1. Bootstrap

```bash
# Nix shell with Weaviate server and weaviate-client
nix develop .#rag-weaviate

# Start Weaviate server (Docker alternative)
weaviate &
# or: docker run -p 8080:8080 -p 50051:50051 semitechnologies/weaviate:latest

# Environment
export CEREBRO_VECTOR_STORE_PROVIDER=weaviate
export WEAVIATE_URL=http://localhost:8080
export WEAVIATE_GRPC_PORT=50051
# export WEAVIATE_API_KEY=...            # for Weaviate Cloud Service
# export WEAVIATE_ENABLE_HYBRID=true     # BM25 + vector hybrid (RRF)

# Initialize collection (COSINE HNSW, idempotent)
cerebro rag backend init
```

---

## 2. Health Check

```bash
cerebro rag backend health

# Direct REST health
curl -s http://localhost:8080/v1/.well-known/ready
# Returns: {}  (200 OK = healthy)

# Node list
curl -s http://localhost:8080/v1/nodes | python3 -m json.tool

# Programmatic
python3 -c "
from cerebro.providers.weaviate import WeaviateVectorStoreProvider
p = WeaviateVectorStoreProvider()
print(p.health_status())
"
```

---

## 3. Backup

```bash
# Trigger a backup (filesystem backend)
curl -X POST http://localhost:8080/v1/backups/filesystem \
  -H "Content-Type: application/json" \
  -d '{
    "id": "cerebro-backup-'$(date +%Y%m%d_%H%M%S)'",
    "include": ["CerebroDocuments"]
  }'

# Check backup status
curl "http://localhost:8080/v1/backups/filesystem/cerebro-backup-20260419_120000"
```

S3 backend:
```json
{
  "id": "cerebro-s3-backup-20260419",
  "include": ["CerebroDocuments"],
  "config": {
    "bucket": "cerebro-weaviate-backups",
    "path": "backups/"
  }
}
```

---

## 4. Restore

```bash
# Restore collection from backup
curl -X POST "http://localhost:8080/v1/backups/filesystem/cerebro-backup-20260419_120000/restore" \
  -H "Content-Type: application/json" \
  -d '{"include": ["CerebroDocuments"]}'

# Check restore status
curl "http://localhost:8080/v1/backups/filesystem/cerebro-backup-20260419_120000/restore"

# Verify
cerebro rag backend health
cerebro rag backend smoke
```

---

## 5. Multi-Tenancy

Weaviate supports first-class multi-tenancy (tenant-per-partition). Cerebro's namespace
isolation uses property-based filters, not Weaviate tenants. To enable Weaviate native
multi-tenancy for strict data isolation between tenants:

```python
# When creating the collection (override initialize_schema)
from weaviate.classes.config import Configure
client.collections.create(
    name="CerebroDocuments",
    multi_tenancy_config=Configure.multi_tenancy(enabled=True),
    ...
)
```

Then supply the tenant name on every operation via the `tenant` parameter.

---

## 6. Rollback

```bash
# Soft rollback: switch backend
export CEREBRO_VECTOR_STORE_PROVIDER=chroma

# Hard rollback: delete collection + restore backup
curl -X DELETE http://localhost:8080/v1/schema/CerebroDocuments
# Then restore from backup (§4)

# Verify
cerebro rag backend health --format json
```

---

## 7. Collection Maintenance

```bash
# Collection object count
curl "http://localhost:8080/v1/objects?class=CerebroDocuments&limit=0" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('total:', d.get('totalResults'))"

# Delete stale objects by filter
curl -X DELETE http://localhost:8080/v1/objects \
  -H "Content-Type: application/json" \
  -d '{"class": "CerebroDocuments", "where": {"path": ["namespace"], "operator": "Equal", "valueText": "stale-project"}}'

# Trigger compaction (background process, no manual trigger needed)
# Monitor via: GET /v1/nodes
```

---

## 8. Hybrid Search

When `WEAVIATE_ENABLE_HYBRID=true`, queries use Weaviate's native hybrid (BM25 + vector RRF):

```bash
export WEAVIATE_ENABLE_HYBRID=true
cerebro rag query "kubernetes ingress controller TLS" --top-k 10
```

The `query_text` kwarg triggers the hybrid path in `WeaviateVectorStoreProvider.search()`.

---

## 9. Monitoring

| Metric | Endpoint |
|--------|----------|
| Readiness | `GET /v1/.well-known/ready` |
| Liveness | `GET /v1/.well-known/live` |
| Node status | `GET /v1/nodes` |
| Object count | `GET /v1/objects?class=CerebroDocuments&limit=0` → `totalResults` |
| Memory (Go pprof) | `GET /debug/pprof/heap` (if enabled) |

Environment variables:
- `WEAVIATE_URL` — HTTP URL (default: `http://localhost:8080`)
- `WEAVIATE_GRPC_PORT` — gRPC port for v4 client (default: `50051`)
- `WEAVIATE_API_KEY` — API key for Weaviate Cloud or secured clusters
- `WEAVIATE_ENABLE_HYBRID` — `"true"` to enable BM25+vector hybrid queries
- `CEREBRO_VECTOR_STORE_COLLECTION_NAME` — collection name (PascalCase auto-applied; default: `cerebro_documents` → `CerebroDocuments`)
- `CEREBRO_VECTOR_STORE_NAMESPACE` — default namespace scope
- `CEREBRO_VECTOR_STORE_EMBEDDING_DIMENSIONS` — vector size (default: 384)
