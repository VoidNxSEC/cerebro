"""Tests for the pgvector-backed vector store provider."""

from cerebro.providers.pgvector import PgVectorStoreProvider


class FakeCursor:
    def __init__(self, *, rows=None):
        self.rows = list(rows or [])
        self.executed: list[tuple[str, object]] = []
        self.rowcount = 0

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if sql.lstrip().upper().startswith("DELETE"):
            self.rowcount = 1

    def executemany(self, sql, rows):
        materialized_rows = list(rows)
        self.executed.append((sql, materialized_rows))
        self.rowcount = len(materialized_rows)

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        if not self.rows:
            return None
        return self.rows[0]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_render_bootstrap_sql_includes_pgvector_index():
    provider = PgVectorStoreProvider(
        dsn="postgresql://localhost/cerebro",
        collection_name="prod-documents",
        default_namespace="prod",
        schema="rag-prod",
        embedding_dimensions=768,
        index_type="hnsw",
    )

    sql = provider.render_bootstrap_sql()

    assert 'CREATE EXTENSION IF NOT EXISTS vector' in sql
    assert '"rag_prod"."prod_documents"' in sql
    assert "vector(768)" in sql
    assert "USING hnsw" in sql


def test_initialize_schema_executes_bootstrap_statements():
    provider = PgVectorStoreProvider(
        dsn="postgresql://localhost/cerebro",
        collection_name="docs",
        schema="rag",
        embedding_dimensions=384,
    )
    cursor = FakeCursor()
    provider._connect = lambda: FakeConnection(cursor)  # type: ignore[method-assign]

    result = provider.initialize_schema()

    assert result["backend"] == "pgvector"
    assert result["initialized"] is True
    executed_sql = "\n".join(sql for sql, _ in cursor.executed)
    assert "CREATE TABLE IF NOT EXISTS" in executed_sql
    assert "vector(384)" in executed_sql


def test_upsert_documents_serializes_metadata_and_embeddings():
    provider = PgVectorStoreProvider(
        dsn="postgresql://localhost/cerebro",
        collection_name="docs",
        default_namespace="prod",
        embedding_dimensions=2,
    )
    cursor = FakeCursor()
    provider._connect = lambda: FakeConnection(cursor)  # type: ignore[method-assign]

    inserted = provider.upsert_documents(
        [
            {
                "id": "intel-1",
                "content": "def hello(): pass",
                "title": "Hello",
                "source": "repo/main.py",
                "type": "techint",
            }
        ],
        [[0.25, 0.75]],
    )

    assert inserted == 1
    statement, rows = cursor.executed[0]
    assert "ON CONFLICT (document_id)" in statement
    row = rows[0]
    assert row[0] == "intel-1"
    assert row[3] == "prod"
    assert row[4] == "[0.25,0.75]"
    assert '"title": "Hello"' in row[2]


def test_search_returns_normalized_results():
    provider = PgVectorStoreProvider(
        dsn="postgresql://localhost/cerebro",
        collection_name="docs",
        default_namespace="prod",
        embedding_dimensions=2,
    )
    cursor = FakeCursor(
        rows=[
            (
                "intel-1",
                "def hello(): pass",
                {"title": "Hello", "source": "repo/main.py"},
                "prod",
                0.05,
            )
        ]
    )
    provider._connect = lambda: FakeConnection(cursor)  # type: ignore[method-assign]

    results = provider.search(
        [0.25, 0.75],
        top_k=3,
        filters={"type": "techint"},
        namespace="prod",
    )

    assert len(results) == 1
    assert results[0].id == "intel-1"
    assert results[0].source == "repo/main.py"
    assert round(results[0].score, 2) == 0.95
    statement, params = cursor.executed[0]
    assert "jsonb_extract_path_text(metadata, %s) = %s" in statement
    assert params[-1] == 3


def test_export_documents_parses_embedding_text():
    provider = PgVectorStoreProvider(
        dsn="postgresql://localhost/cerebro",
        collection_name="docs",
        default_namespace="prod",
        embedding_dimensions=2,
    )
    cursor = FakeCursor(
        rows=[
            (
                "intel-1",
                "def hello(): pass",
                {"title": "Hello", "source": "repo/main.py"},
                "prod",
                "[0.25,0.75]",
            )
        ]
    )
    provider._connect = lambda: FakeConnection(cursor)  # type: ignore[method-assign]

    exported = provider.export_documents(namespace="prod", limit=10, offset=5)

    assert len(exported) == 1
    assert exported[0].id == "intel-1"
    assert exported[0].embedding == [0.25, 0.75]
    statement, params = cursor.executed[0]
    assert "embedding::text" in statement
    assert params[-2:] == [10, 5]
