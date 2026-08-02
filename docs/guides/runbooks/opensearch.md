# OpenSearch / Elasticsearch Operational Runbook

**Backend:** `opensearch` (aliases: `elasticsearch`, `elastic`, `open-search`)  
**When to choose:** You already run OpenSearch or Elasticsearch, need hybrid BM25+vector search
(`OPENSEARCH_ENABLE_HYBRID=true`), or have existing full-text search infrastructure to extend.  
**When NOT to choose:** Pure vector workloads where k-NN latency matters more than full-text
ranking — Qdrant or Weaviate will be faster at pure ANN retrieval.

---

## 1. Bootstrap

```bash
# Nix shell with OpenSearch server and opensearch-py
nix develop .#rag-opensearch

# Start OpenSearch (Docker alternative)
opensearch &
# or: docker run -p 9200:9200 -e "discovery.type=single-node" opensearchproject/opensearch:latest

# Environment
export CEREBRO_VECTOR_STORE_PROVIDER=opensearch
export OPENSEARCH_URL=http://localhost:9200
# export OPENSEARCH_USERNAME=admin
# export OPENSEARCH_PASSWORD=admin
# export OPENSEARCH_ENABLE_HYBRID=true    # BM25 + vector hybrid
# export OPENSEARCH_ES_COMPAT=true        # Elasticsearch 8.x mode (dense_vector)

# Initialize index (idempotent)
cerebro rag backend init
```

Manual index creation:
```json
PUT /cerebro_documents
{
  "settings": { "index.knn": true },
  "mappings": {
    "properties": {
      "content": { "type": "text" },
      "embedding": {
        "type": "knn_vector",
        "dimension": 384,
        "method": { "name": "hnsw", "space_type": "cosinesimil", "engine": "nmslib" }
      },
      "namespace": { "type": "keyword" },
      "source":    { "type": "keyword" }
    }
  }
}
```

---

## 2. Health Check

```bash
cerebro rag backend health

# Cluster health
curl -s http://localhost:9200/_cluster/health | python3 -m json.tool

# Index stats
curl -s "http://localhost:9200/cerebro_documents/_stats" | python3 -m json.tool
```

---

## 3. Backup (Snapshot Repository)

```bash
# Register a filesystem snapshot repository
curl -X PUT "http://localhost:9200/_snapshot/cerebro_backups" \
  -H 'Content-Type: application/json' -d '{
    "type": "fs",
    "settings": { "location": "/mnt/snapshots/cerebro" }
  }'

# Create a snapshot
curl -X PUT "http://localhost:9200/_snapshot/cerebro_backups/snapshot_$(date +%Y%m%d_%H%M%S)?wait_for_completion=true" \
  -H 'Content-Type: application/json' -d '{
    "indices": "cerebro_documents",
    "include_global_state": false
  }'

# List snapshots
curl "http://localhost:9200/_snapshot/cerebro_backups/_all" | python3 -m json.tool
```

For S3-backed repositories:
```json
{
  "type": "s3",
  "settings": {
    "bucket": "cerebro-snapshots",
    "region": "us-east-1"
  }
}
```

---

## 4. Restore

```bash
# Close index before restore
curl -X POST "http://localhost:9200/cerebro_documents/_close"

# Restore from snapshot
curl -X POST "http://localhost:9200/_snapshot/cerebro_backups/snapshot_20260419_120000/_restore" \
  -H 'Content-Type: application/json' -d '{
    "indices": "cerebro_documents",
    "rename_pattern": "(.+)",
    "rename_replacement": "$1_restore"
  }'

# Reopen index
curl -X POST "http://localhost:9200/cerebro_documents_restore/_open"

# Verify doc count
curl "http://localhost:9200/cerebro_documents_restore/_count"
```

---

## 5. Index Alias Rollback

Use index aliases for zero-downtime rollback:
```bash
# Point alias to current index
curl -X POST "http://localhost:9200/_aliases" -d '{
  "actions": [{ "add": { "index": "cerebro_documents_v2", "alias": "cerebro_documents" } }]
}'

# Rollback: swap alias back to previous index
curl -X POST "http://localhost:9200/_aliases" -d '{
  "actions": [
    { "remove": { "index": "cerebro_documents_v2", "alias": "cerebro_documents" } },
    { "add":    { "index": "cerebro_documents_v1", "alias": "cerebro_documents" } }
  ]
}'
```

---

## 6. Migration

```bash
export CEREBRO_VECTOR_STORE_PROVIDER=opensearch
cerebro rag backend migrate \
    --from-provider chroma \
    --from-persist-directory ./data/vector_db \
    --batch-size 200

# Enable hybrid mode after migration
export OPENSEARCH_ENABLE_HYBRID=true
cerebro rag backend smoke
```

---

## 7. Monitoring

| Metric | Command |
|--------|---------|
| Document count | `GET /cerebro_documents/_count` |
| Index size | `GET /cerebro_documents/_stats/store` |
| k-NN cache stats | `GET /_plugins/_knn/stats` |
| Cluster health | `GET /_cluster/health` |

Environment variables:
- `OPENSEARCH_URL` — server URL (default: `http://localhost:9200`)
- `OPENSEARCH_USERNAME` / `OPENSEARCH_PASSWORD` — basic auth
- `OPENSEARCH_API_KEY` — API key auth (alternative to basic)
- `OPENSEARCH_ENABLE_HYBRID` — `"true"` for BM25+vector hybrid queries
- `OPENSEARCH_ES_COMPAT` — `"true"` for Elasticsearch 8.x `dense_vector` mapping
- `CEREBRO_VECTOR_STORE_COLLECTION_NAME` — index name (default: `cerebro_documents`)
