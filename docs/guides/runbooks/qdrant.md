# Qdrant Operational Runbook

**Backend:** `qdrant`  
**When to choose:** Pure vector workloads, >10M documents, single-purpose vector DB with
sub-millisecond latency, in-memory or on-disk segments, no SQL dependency.  
**When NOT to choose:** You need SQL joins, ACID cross-collection transactions, or your
infrastructure already runs only PostgreSQL.

---

## 1. Bootstrap

```bash
# Nix shell with Qdrant server and qdrant-client
nix develop .#rag-qdrant

# Start Qdrant server (Docker alternative)
qdrant &  # or: docker run -p 6333:6333 qdrant/qdrant

# Set environment
export CEREBRO_VECTOR_STORE_PROVIDER=qdrant
export QDRANT_URL=http://localhost:6333
# export QDRANT_API_KEY=...   # for Qdrant Cloud

# Initialize collection (COSINE HNSW, idempotent)
cerebro rag backend init
```

---

## 2. Health Check

```bash
cerebro rag backend health

# Via REST API
curl -s http://localhost:6333/healthz

# Programmatic
python3 -c "
from cerebro.providers.qdrant import QdrantVectorStoreProvider
p = QdrantVectorStoreProvider()
print(p.health_status())
"
```

---

## 3. Backup (Snapshots)

```bash
# Create a collection snapshot
curl -X POST "http://localhost:6333/collections/cerebro_documents/snapshots"
# Returns: {"result": {"name": "cerebro_documents-TIMESTAMP.snapshot", ...}}

# List snapshots
curl "http://localhost:6333/collections/cerebro_documents/snapshots"

# Download snapshot
curl -o cerebro_documents.snapshot \
    "http://localhost:6333/collections/cerebro_documents/snapshots/cerebro_documents-TIMESTAMP.snapshot"
```

For Qdrant Cloud, snapshots are managed via the Cloud Console or Qdrant REST API with your API key.

---

## 4. Restore

```bash
# Upload snapshot to a running Qdrant instance
curl -X POST "http://localhost:6333/collections/cerebro_documents/snapshots/upload?priority=snapshot" \
    -H "Content-Type: multipart/form-data" \
    -F "snapshot=@cerebro_documents.snapshot"

# Verify
curl "http://localhost:6333/collections/cerebro_documents" | python3 -m json.tool
```

---

## 5. Migration

```bash
# Migrate from Chroma to Qdrant
export CEREBRO_VECTOR_STORE_PROVIDER=qdrant
cerebro rag backend migrate \
    --from-provider chroma \
    --from-persist-directory ./data/vector_db \
    --batch-size 200

# Cross-namespace migration
cerebro rag backend migrate \
    --from-provider pgvector \
    --from-url "postgresql+psycopg://user:pass@host/db" \
    --from-namespace production \
    --batch-size 500
```

---

## 6. Rollback

```bash
# Switch active backend
export CEREBRO_VECTOR_STORE_PROVIDER=chroma

# Delete collection and restore from snapshot
curl -X DELETE "http://localhost:6333/collections/cerebro_documents"
# Then restore snapshot (see §4)

# Verify
cerebro rag backend smoke
```

---

## 7. Collection Maintenance

```bash
# Optimize collection (merges segments, reduces memory)
curl -X POST "http://localhost:6333/collections/cerebro_documents/index"

# Collection info (size, vector count, segments)
curl "http://localhost:6333/collections/cerebro_documents" | python3 -m json.tool

# Cluster info (multi-node)
curl "http://localhost:6333/cluster" | python3 -m json.tool
```

---

## 8. Monitoring

| Metric | Endpoint |
|--------|----------|
| Vector count | `GET /collections/cerebro_documents` → `result.vectors_count` |
| Indexed count | `result.indexed_vectors_count` |
| Disk usage | `result.disk_usage_bytes` |
| RAM usage | `result.ram_usage_bytes` |
| Cluster health | `GET /cluster` |

Environment variables:
- `QDRANT_URL` — server URL (default: `http://localhost:6333`)
- `QDRANT_API_KEY` — API key for Qdrant Cloud / secured clusters
- `CEREBRO_VECTOR_STORE_COLLECTION_NAME` — collection name (default: `cerebro_documents`)
- `CEREBRO_VECTOR_STORE_NAMESPACE` — default namespace scope
- `CEREBRO_VECTOR_STORE_EMBEDDING_DIMENSIONS` — vector size (default: 384)
