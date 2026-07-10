"""
pgvector Vector Store Provider

Production-oriented vector storage using PostgreSQL + pgvector.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, ClassVar

from cerebro.interfaces.vector_store import (
    MetadataFilters,
    StoredVectorDocument,
    VectorSearchResult,
    VectorStoreProvider,
)

logger = logging.getLogger("cerebro.providers.pgvector")


class PgVectorStoreProvider(VectorStoreProvider):
    """Vector store provider backed by PostgreSQL with the pgvector extension."""

    backend_name = "pgvector"
    DEFAULT_COLLECTION_NAME = "cerebro_documents"
    SUPPORTED_INDEX_TYPES: ClassVar[set[str]] = {"hnsw", "ivfflat", "none"}
    _IDENTIFIER_PATTERN = re.compile(r"[^a-zA-Z0-9_]+")

    def __init__(
        self,
        dsn: str | None = None,
        collection_name: str | None = None,
        default_namespace: str | None = None,
        schema: str = "public",
        embedding_dimensions: int | None = None,
        index_type: str = "hnsw",
    ):
        self.dsn = dsn
        self.default_namespace = default_namespace
        self.collection_name = collection_name or self.DEFAULT_COLLECTION_NAME
        self.schema = self._normalize_identifier(schema, fallback="public")
        self.table_name = self._normalize_identifier(
            self.collection_name,
            fallback=self.DEFAULT_COLLECTION_NAME,
        )
        self.embedding_dimensions = embedding_dimensions
        self.index_type = (index_type or "hnsw").strip().lower()

        if self.embedding_dimensions is not None and self.embedding_dimensions <= 0:
            raise ValueError("embedding_dimensions must be positive when provided.")

        if self.index_type not in self.SUPPORTED_INDEX_TYPES:
            supported = ", ".join(sorted(self.SUPPORTED_INDEX_TYPES))
            raise ValueError(
                f"Unsupported pgvector index type: {index_type!r}. Supported values: {supported}."
            )

    def initialize_schema(self, **kwargs) -> dict[str, Any]:
        """Create the pgvector extension, schema, table, and indexes if needed."""

        sql = self.render_bootstrap_sql()
        with self._connect() as connection:
            with connection.cursor() as cursor:
                for statement in self._split_statements(sql):
                    cursor.execute(statement)

        return {
            **self.get_backend_info(),
            "initialized": True,
            "table_name": self.table_name,
        }

    def add_documents(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[list[float]],
        namespace: str | None = None,
        **kwargs,
    ) -> int:
        """Insert documents into PostgreSQL using idempotent upsert semantics."""

        return self.upsert_documents(
            documents,
            embeddings,
            namespace=namespace,
            **kwargs,
        )

    def upsert_documents(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[list[float]],
        namespace: str | None = None,
        **kwargs,
    ) -> int:
        """Upsert documents and embeddings into the pgvector table."""

        self._validate_document_batch(documents, embeddings)
        if not documents:
            return 0

        statement = f"""
            INSERT INTO {self._qualified_table_name()}
                (document_id, content, metadata, namespace, embedding, updated_at)
            VALUES (%s, %s, %s::jsonb, %s, %s::vector, NOW())
            ON CONFLICT (document_id)
            DO UPDATE SET
                content = EXCLUDED.content,
                metadata = EXCLUDED.metadata,
                namespace = EXCLUDED.namespace,
                embedding = EXCLUDED.embedding,
                updated_at = NOW()
        """
        rows = [
            self._prepare_upsert_row(document, embeddings[index], namespace, index)
            for index, document in enumerate(documents)
        ]

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(statement, rows)

        return len(rows)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: MetadataFilters | None = None,
        namespace: str | None = None,
        min_score: float | None = None,
        **kwargs,
    ) -> list[VectorSearchResult]:
        """Search for similar documents using cosine distance."""

        if top_k <= 0:
            return []

        query_vector = self._serialize_embedding(query_embedding)
        where_clauses = ["TRUE"]
        where_params: list[Any] = []

        resolved_namespace = namespace or self.default_namespace
        if resolved_namespace:
            where_clauses.append("namespace = %s")
            where_params.append(resolved_namespace)

        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                where_clauses.append("jsonb_extract_path_text(metadata, %s) = %s")
                where_params.extend([key, self._stringify_filter_value(value)])

        statement = f"""
            SELECT
                document_id,
                content,
                metadata,
                namespace,
                embedding <=> %s::vector AS distance
            FROM {self._qualified_table_name()}
            WHERE {' AND '.join(where_clauses)}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        params = [query_vector, *where_params, query_vector, top_k]

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement, params)
                rows = cursor.fetchall()

        results: list[VectorSearchResult] = []
        for document_id, content, metadata, row_namespace, distance in rows:
            similarity = 1 - float(distance)
            if min_score is not None and similarity < min_score:
                continue

            metadata_dict = self._coerce_metadata(metadata)
            results.append(
                VectorSearchResult(
                    id=str(document_id),
                    content=str(content or ""),
                    metadata=metadata_dict,
                    score=similarity,
                    distance=float(distance),
                    namespace=row_namespace,
                    title=metadata_dict.get("title"),
                    source=metadata_dict.get("source"),
                )
            )

        return results

    def delete_documents(
        self,
        document_ids: list[str],
        namespace: str | None = None,
    ) -> int:
        """Delete documents by id, optionally scoped by namespace."""

        if not document_ids:
            return 0

        placeholders = ", ".join(["%s"] * len(document_ids))
        where_clauses = [f"document_id IN ({placeholders})"]
        params: list[Any] = list(document_ids)

        resolved_namespace = namespace or self.default_namespace
        if resolved_namespace:
            where_clauses.insert(0, "namespace = %s")
            params.insert(0, resolved_namespace)

        statement = f"""
            DELETE FROM {self._qualified_table_name()}
            WHERE {' AND '.join(where_clauses)}
        """

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement, params)
                deleted = cursor.rowcount

        return max(deleted, 0)

    def clear(self, namespace: str | None = None) -> None:
        """Clear documents from the table, optionally scoped by namespace."""

        resolved_namespace = namespace or self.default_namespace
        statement = f"DELETE FROM {self._qualified_table_name()}"
        params: list[Any] = []

        if resolved_namespace:
            statement += " WHERE namespace = %s"
            params.append(resolved_namespace)

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement, params)

    def get_document_count(self, namespace: str | None = None) -> int:
        """Return the total number of indexed documents."""

        resolved_namespace = namespace or self.default_namespace
        statement = f"SELECT COUNT(*) FROM {self._qualified_table_name()}"
        params: list[Any] = []

        if resolved_namespace:
            statement += " WHERE namespace = %s"
            params.append(resolved_namespace)

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement, params)
                row = cursor.fetchone()

        return int(row[0] if row else 0)

    def export_documents(
        self,
        namespace: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[StoredVectorDocument]:
        """Export stored documents and embeddings for backend migration."""

        resolved_namespace = namespace or self.default_namespace
        where_clauses = ["TRUE"]
        params: list[Any] = []

        if resolved_namespace:
            where_clauses.append("namespace = %s")
            params.append(resolved_namespace)

        statement = f"""
            SELECT
                document_id,
                content,
                metadata,
                namespace,
                embedding::text
            FROM {self._qualified_table_name()}
            WHERE {' AND '.join(where_clauses)}
            ORDER BY document_id
            LIMIT %s
            OFFSET %s
        """
        params.extend([limit, offset])

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement, params)
                rows = cursor.fetchall()

        exported: list[StoredVectorDocument] = []
        for document_id, content, metadata, row_namespace, embedding_raw in rows:
            metadata_dict = self._coerce_metadata(metadata)
            exported.append(
                StoredVectorDocument(
                    id=str(document_id),
                    content=str(content or ""),
                    metadata=metadata_dict,
                    embedding=self._deserialize_embedding(embedding_raw),
                    namespace=row_namespace,
                    title=metadata_dict.get("title"),
                    source=metadata_dict.get("source"),
                )
            )

        return exported

    def health_check(self) -> bool:
        """Verify the PostgreSQL backend is reachable."""

        if not self.dsn:
            return False

        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            return True
        except Exception as exc:
            logger.warning("pgvector health check failed: %s", exc)
            return False

    def get_backend_info(self) -> dict[str, Any]:
        """Return pgvector backend metadata without leaking credentials."""

        return {
            "backend": self.backend_name,
            "collection_name": self.collection_name,
            "schema": self.schema,
            "table_name": self.table_name,
            "default_namespace": self.default_namespace,
            "embedding_dimensions": self.embedding_dimensions,
            "index_type": self.index_type,
            "dsn_configured": bool(self.dsn),
            "supports_filters": True,
            "supports_namespace": True,
        }

    def render_bootstrap_sql(self) -> str:
        """Render the SQL bootstrap template with the configured identifiers."""

        bootstrap_template = self._bootstrap_template_path().read_text(encoding="utf-8")
        replacements = {
            "{{SCHEMA_NAME}}": self._quote_identifier(self.schema),
            "{{TABLE_NAME}}": self._qualified_table_name(),
            "{{VECTOR_TYPE}}": self._vector_type_sql(),
            "{{NAMESPACE_INDEX_NAME}}": self._quote_identifier(
                self._normalize_identifier(f"{self.table_name}_namespace_idx")
            ),
            "{{METADATA_INDEX_NAME}}": self._quote_identifier(
                self._normalize_identifier(f"{self.table_name}_metadata_gin_idx")
            ),
            "{{VECTOR_INDEX_SQL}}": self._vector_index_sql(),
        }

        rendered = bootstrap_template
        for placeholder, value in replacements.items():
            rendered = rendered.replace(placeholder, value)
        return rendered

    def _prepare_upsert_row(
        self,
        document: dict[str, Any],
        embedding: list[float],
        namespace: str | None,
        index: int,
    ) -> tuple[str, str, str, str | None, str]:
        resolved_namespace = namespace or self.default_namespace
        document_namespace = self._resolve_document_namespace(document, resolved_namespace)
        metadata = {
            key: self._normalize_metadata_value(value)
            for key, value in document.items()
            if key not in {"content", "text", "id"}
        }
        if document_namespace:
            metadata["namespace"] = document_namespace

        document_id = str(document.get("id", f"doc_{index}"))
        content = str(document.get("content", document.get("text", "")))
        metadata_json = json.dumps(metadata, ensure_ascii=True, sort_keys=True)

        return (
            document_id,
            content,
            metadata_json,
            document_namespace,
            self._serialize_embedding(embedding),
        )

    def _qualified_table_name(self) -> str:
        return f"{self._quote_identifier(self.schema)}.{self._quote_identifier(self.table_name)}"

    def _vector_type_sql(self) -> str:
        if self.embedding_dimensions:
            return f"vector({self.embedding_dimensions})"
        return "vector"

    def _vector_index_sql(self) -> str:
        if self.index_type == "none" or self.embedding_dimensions is None:
            return "-- vector index skipped until embedding dimensions are configured"

        index_name = self._quote_identifier(
            self._normalize_identifier(f"{self.table_name}_embedding_{self.index_type}_idx")
        )
        base = (
            f"CREATE INDEX IF NOT EXISTS {index_name}\n"
            f"    ON {self._qualified_table_name()} USING {self.index_type} "
            "(embedding vector_cosine_ops)"
        )

        if self.index_type == "ivfflat":
            return f"{base} WITH (lists = 100);"

        return f"{base};"

    def _validate_document_batch(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Number of documents ({len(documents)}) must match "
                f"number of embeddings ({len(embeddings)})."
            )

        if self.embedding_dimensions is None:
            return

        for embedding in embeddings:
            if len(embedding) != self.embedding_dimensions:
                raise ValueError(
                    "Embedding dimension mismatch for pgvector backend: "
                    f"expected {self.embedding_dimensions}, got {len(embedding)}."
                )

    @classmethod
    def _normalize_identifier(cls, value: str, fallback: str | None = None) -> str:
        normalized = cls._IDENTIFIER_PATTERN.sub("_", value.strip().lower()).strip("_")
        if not normalized:
            if fallback is None:
                raise ValueError("SQL identifier cannot be empty.")
            normalized = fallback
        if normalized[0].isdigit():
            normalized = f"v_{normalized}"
        return normalized

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        return f'"{identifier}"'

    @staticmethod
    def _normalize_metadata_value(value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return json.dumps(value, ensure_ascii=True)

    @staticmethod
    def _stringify_filter_value(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    @staticmethod
    def _coerce_metadata(metadata: Any) -> dict[str, Any]:
        if isinstance(metadata, dict):
            return metadata
        if isinstance(metadata, str):
            try:
                parsed = json.loads(metadata)
            except json.JSONDecodeError:
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    @staticmethod
    def _serialize_embedding(embedding: list[float]) -> str:
        return "[" + ",".join(f"{float(value):.12g}" for value in embedding) + "]"

    @staticmethod
    def _deserialize_embedding(raw_embedding: Any) -> list[float]:
        if isinstance(raw_embedding, str):
            try:
                parsed = json.loads(raw_embedding)
            except json.JSONDecodeError:
                return []
            return [float(value) for value in parsed]
        if isinstance(raw_embedding, (list, tuple)):
            return [float(value) for value in raw_embedding]
        return []

    @staticmethod
    def _split_statements(sql: str) -> list[str]:
        statements: list[str] = []
        for statement in sql.split(";"):
            stripped = statement.strip()
            if not stripped or stripped.startswith("--"):
                continue
            statements.append(stripped)
        return statements

    @staticmethod
    def _bootstrap_template_path() -> Path:
        return Path(__file__).with_name("bootstrap.sql")

    @staticmethod
    def _resolve_document_namespace(
        document: dict[str, Any],
        fallback_namespace: str | None,
    ) -> str | None:
        explicit_namespace = document.get("namespace")
        if isinstance(explicit_namespace, str) and explicit_namespace.strip():
            return explicit_namespace
        return fallback_namespace

    def _connect(self):
        dsn = self.dsn
        if not dsn:
            raise ValueError(
                "CEREBRO_VECTOR_STORE_URL must be configured for the pgvector backend."
            )

        try:
            import psycopg
        except ImportError as exc:
            raise ImportError(
                "psycopg is required for the pgvector backend. "
                "Re-enter the project with `nix develop --command ...` so the "
                "PostgreSQL driver is available."
            ) from exc

        return psycopg.connect(dsn)
