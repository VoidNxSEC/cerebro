# Backend Selection Guide

**When to choose which vector store for Cerebro.**

---

## Decision Tree

```
Are you prototyping or running a small team demo?
├─ Yes → ChromaDB (default, no setup required)
└─ No ↓

Do you already run PostgreSQL in production?
├─ Yes → pgvector (single operational surface, SQL metadata queries)
└─ No ↓

Do you need hybrid (BM25 + vector) search?
├─ Yes + managed cloud preferred → OpenSearch (AWS, Aiven)
├─ Yes + local-first, no cloud → Weaviate (Nix shell, open-source)
└─ No ↓

Do you operate on Azure?
├─ Yes → Azure AI Search (managed, HNSW, OData filters)
└─ No ↓

Pure vector workload at >10M documents?
└─ Yes → Qdrant (dedicated vector DB, best recall/latency ratio)
```

---

## Backend Comparison

| Criterion | chroma | pgvector | qdrant | opensearch | azure_search | weaviate |
|-----------|:------:|:--------:|:------:|:----------:|:------------:|:--------:|
| **Setup complexity** | None | Low (Postgres) | Low | Medium | Medium | Low |
| **Hybrid search** | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| **Metadata filters** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Namespace isolation** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **SQL / relational joins** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **ACID guarantees** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Scale (docs)** | <1M | <50M | >50M | >50M | >50M | >50M |
| **Cloud-managed option** | ❌ | RDS/Supabase | Qdrant Cloud | AWS/Aiven | Azure (SaaS) | Weaviate Cloud |
| **Local Nix dev shell** | ❌ (default) | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Stored vectors exportable** | ✅ | ✅ | ✅ | ✅ | ❌* | ✅ |
| **Production ready** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |

*Azure AI Search does not return stored vectors via the search API — content-only export.

---

## 1. ChromaDB — Development Only

```bash
export CEREBRO_VECTOR_STORE_PROVIDER=chroma
export CEREBRO_VECTOR_STORE_PERSIST_DIRECTORY=./data/vector_db
```

- **Use when:** local development, quick demos, CI smoke tests.
- **Do not use when:** multi-user, production traffic, >500k documents.
- No Nix shell or runbook required — it just works out of the box.

---

## 2. pgvector — SQL-Integrated Production

```bash
export CEREBRO_VECTOR_STORE_PROVIDER=pgvector
export CEREBRO_VECTOR_STORE_URL="postgresql+psycopg://user:pass@host/dbname"
```

**Choose pgvector when:**
- Your team already operates PostgreSQL (RDS, Cloud SQL, Supabase, self-hosted).
- You need ACID guarantees, SQL-level metadata queries, or JOIN with relational data.
- You want a single operational surface (one backup job, one connection pool, one DBA team).

**Do not choose pgvector when:**
- Your document count exceeds 50M — Postgres HNSW starts to slow down.
- You need hybrid BM25+vector search.

Nix shell: `nix develop .#rag-pgvector`  
Runbook: `docs/guides/runbooks/pgvector.md`

---

## 3. Qdrant — Dedicated Vector DB

```bash
export CEREBRO_VECTOR_STORE_PROVIDER=qdrant
export QDRANT_URL=http://localhost:6333
export QDRANT_API_KEY=...   # for Qdrant Cloud
```

**Choose Qdrant when:**
- Pure vector workload, 10M–500M+ documents.
- You need the best recall/latency trade-off without BM25.
- You want a simple HTTP/gRPC API with no database administration overhead.

**Do not choose Qdrant when:**
- You need BM25 hybrid search (use OpenSearch or Weaviate).
- You need SQL-level queries on metadata (use pgvector).

Nix shell: `nix develop .#rag-qdrant`  
Runbook: `docs/guides/runbooks/qdrant.md`

---

## 4. OpenSearch — Hybrid Search at Scale

```bash
export CEREBRO_VECTOR_STORE_PROVIDER=opensearch
export OPENSEARCH_URL=http://localhost:9200
export OPENSEARCH_ENABLE_HYBRID=true     # activate BM25+knn hybrid
export OPENSEARCH_ES_COMPAT=true         # for Elasticsearch 8.x
```

**Choose OpenSearch when:**
- You need hybrid BM25+vector search (full-text + semantic).
- You already operate OpenSearch/Elasticsearch for log aggregation or search.
- You want AWS OpenSearch Service (managed) with IAM auth.

**Do not choose OpenSearch when:**
- Operational overhead of Elasticsearch is not justified for the scale.
- You want local Nix-only development without a JVM service.

Nix shell: `nix develop .#rag-opensearch`  
Runbook: `docs/guides/runbooks/opensearch.md`

---

## 5. Azure AI Search — Azure-Native

```bash
export CEREBRO_VECTOR_STORE_PROVIDER=azure_search
export AZURE_SEARCH_ENDPOINT=https://<resource>.search.windows.net
export AZURE_SEARCH_INDEX_NAME=cerebro-documents
export AZURE_SEARCH_API_KEY=...
```

**Choose Azure AI Search when:**
- Your workload runs on Azure and you want a managed, serverless vector service.
- You use Azure AD / RBAC and need native integration.
- You want automatic scaling without managing servers.

**Do not choose Azure AI Search when:**
- You need stored vectors to be exportable (Azure Search does not return vectors via API).
- You run a hybrid BM25+vector pipeline — Azure AI Search supports semantic ranker as an add-on, not a native BM25 hybrid.
- You need a local development environment (no Nix server package available).

Runbook: `docs/guides/runbooks/azure_search.md`

---

## 6. Weaviate — Hybrid Search, Local-First

```bash
export CEREBRO_VECTOR_STORE_PROVIDER=weaviate
export WEAVIATE_URL=http://localhost:8080
export WEAVIATE_ENABLE_HYBRID=true       # activate BM25+vector RRF
```

**Choose Weaviate when:**
- You want hybrid BM25+vector search with a modern open-source stack.
- You prefer a local-first workflow (Nix shell, no cloud account required).
- You need multi-tenancy at the collection level (Weaviate first-class feature).

**Do not choose Weaviate when:**
- You already run PostgreSQL and want a single operational surface.
- Your team is not comfortable with a JVM/Go hybrid service.

Nix shell: `nix develop .#rag-weaviate`  
Runbook: `docs/guides/runbooks/weaviate.md`

---

## Migration Path

Cerebro supports live migration between backends via `export_documents()` /
`upsert_documents()`:

```bash
# Migrate from Chroma (dev) → pgvector (prod)
cerebro rag backend migrate \
  --from-provider chroma \
  --from-persist-directory ./data/vector_db \
  --batch-size 200

# Migrate pgvector → Qdrant (scaling up)
cerebro rag backend migrate \
  --from-provider pgvector \
  --to-provider qdrant \
  --batch-size 500
```

All backends implement `export_documents()` with embeddings (except Azure AI
Search — content only). Migration is idempotent: re-running skips unchanged chunks
once content-hash dedup is implemented (§8 of TODO_PLAN).

---

## Aliases

The factory accepts multiple aliases for each provider:

| You type | Resolves to |
|----------|------------|
| `chroma`, `chromadb`, `local` | `chroma` |
| `pgvector`, `postgres`, `postgresql` | `pgvector` |
| `qdrant` | `qdrant` |
| `opensearch`, `elasticsearch`, `elastic` | `opensearch` |
| `azure_search`, `azure-search`, `cognitive-search` | `azure_search` |
| `weaviate` | `weaviate` |
