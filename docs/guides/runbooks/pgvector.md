# pgvector Operational Runbook

**Backend:** `pgvector`  
**When to choose:** You already run PostgreSQL (or AWS RDS, Cloud SQL, Supabase), want SQL-level
metadata queries, ACID guarantees, and a single operational surface for both
relational and vector data.  
**When NOT to choose:** Vector-only workloads at >50M documents — a dedicated vector DB
(Qdrant, Weaviate) will outperform at that scale.

---

## 1. Bootstrap

```bash
# Nix shell with PostgreSQL and psycopg
nix develop .#rag-pgvector

# Set DSN
export CEREBRO_VECTOR_STORE_PROVIDER=pgvector
export CEREBRO_VECTOR_STORE_URL="postgresql+psycopg://cerebro:secret@localhost/cerebro_db"
export CEREBRO_VECTOR_STORE_COLLECTION_NAME=cerebro_documents

# Initialize schema (idempotent)
cerebro rag backend init
# Creates: CREATE EXTENSION vector; CREATE TABLE; CREATE INDEX (HNSW)
```

Manual SQL (emergency fallback):
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS cerebro_documents (
    id          TEXT PRIMARY KEY,
    content     TEXT NOT NULL,
    embedding   vector(384),
    metadata    JSONB DEFAULT '{}'::jsonb,
    namespace   TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS cerebro_documents_hnsw_idx
    ON cerebro_documents USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

---

## 2. Health Check

```bash
cerebro rag backend health

# Or programmatically:
python3 -c "
from cerebro.providers.pgvector import PgVectorStoreProvider
p = PgVectorStoreProvider()
print(p.health_status())
"
```

Expected output: `VectorStoreHealth(healthy=True, backend='pgvector', details={...})`

---

## 3. Backup

### Logical backup (recommended)
```bash
# Full database dump
pg_dump -Fc -d cerebro_db -f cerebro_db_$(date +%Y%m%d_%H%M%S).dump

# Table-only (lighter, no schema)
pg_dump -Fc -d cerebro_db -t cerebro_documents \
    -f cerebro_docs_$(date +%Y%m%d_%H%M%S).dump
```

### Continuous backup (production)
Enable WAL archiving or use `pgBackRest` / `Barman`:
```bash
# pgBackRest stanza backup
pgbackrest --stanza=cerebro backup --type=full
```

---

## 4. Restore

```bash
# Stop ingestion traffic first
# Restore from dump
pg_restore -d cerebro_db_restore -Fc cerebro_db_20260419_120000.dump

# Verify row count
psql -d cerebro_db_restore -c "SELECT COUNT(*) FROM cerebro_documents;"

# Rebuild HNSW index after bulk restore
psql -d cerebro_db_restore -c "
REINDEX INDEX cerebro_documents_hnsw_idx;
"
```

---

## 5. Migration Between Namespaces

```bash
# Migrate all Chroma documents → pgvector
cerebro rag backend migrate \
    --from-provider chroma \
    --from-persist-directory ./data/vector_db \
    --batch-size 200

# Migrate specific namespace
cerebro rag backend migrate \
    --from-provider chroma \
    --from-namespace project-x \
    --batch-size 100
```

---

## 6. Rollback

```bash
# Switch back to Chroma (no data loss)
export CEREBRO_VECTOR_STORE_PROVIDER=chroma

# Hard rollback: truncate and restore from dump
psql -d cerebro_db -c "TRUNCATE TABLE cerebro_documents RESTART IDENTITY;"
pg_restore -d cerebro_db --data-only -t cerebro_documents -Fc backup.dump

# Verify
cerebro rag backend health
cerebro rag backend smoke
```

---

## 7. Index Maintenance

```bash
# VACUUM + ANALYZE (run weekly on large tables)
psql -d cerebro_db -c "VACUUM ANALYZE cerebro_documents;"

# Check index health
psql -d cerebro_db -c "
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE tablename = 'cerebro_documents';
"

# Rebuild index if bloated
psql -d cerebro_db -c "REINDEX INDEX CONCURRENTLY cerebro_documents_hnsw_idx;"
```

---

## 8. Monitoring

| Metric | Query |
|--------|-------|
| Row count | `SELECT COUNT(*) FROM cerebro_documents;` |
| Namespace breakdown | `SELECT namespace, COUNT(*) FROM cerebro_documents GROUP BY 1;` |
| Index size | `SELECT pg_size_pretty(pg_relation_size('cerebro_documents_hnsw_idx'));` |
| Table size | `SELECT pg_size_pretty(pg_total_relation_size('cerebro_documents'));` |

Environment variables:
- `CEREBRO_VECTOR_STORE_URL` — PostgreSQL DSN
- `CEREBRO_VECTOR_STORE_COLLECTION_NAME` — table name (default: `cerebro_documents`)
- `CEREBRO_VECTOR_STORE_NAMESPACE` — default namespace scope
- `CEREBRO_VECTOR_STORE_EMBEDDING_DIMENSIONS` — vector size (default: 384)
- `CEREBRO_VECTOR_STORE_INDEX_TYPE` — `hnsw` (default) or `ivfflat`
