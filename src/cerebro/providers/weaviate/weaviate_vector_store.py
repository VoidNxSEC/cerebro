"""
Weaviate Vector Store Provider

Cloud-native, schema-optional vector store backed by Weaviate.
Supports local (embedded / Docker) and Weaviate Cloud Service (WCS) deployments.
Requires the `weaviate-client>=4.9` package.

Namespace isolation is implemented via a filterable `namespace` property.
String document IDs are mapped to deterministic UUIDs (UUID5) because Weaviate
object IDs must be UUIDs. The original string ID is preserved in the `_cerebro_id`
property so round-trips are lossless.

Score normalisation:
    COSINE distance d ∈ [0, 2]  →  certainty = 1 − d/2  ∈ [0, 1]
    Weaviate returns certainty directly; we use it as the normalised score.

Hybrid search (optional, BM25 + vector):
    Activated when WEAVIATE_ENABLE_HYBRID=true AND `query_text` is passed as
    a kwarg to search().  Returns Weaviate's combined reciprocal-rank-fusion
    score in [0, 1].
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, ClassVar
from urllib.parse import urlparse

from cerebro.interfaces.vector_store import (
    MetadataFilters,
    StoredVectorDocument,
    VectorSearchResult,
    VectorStoreProvider,
)

logger = logging.getLogger("cerebro.providers.weaviate")

_CEREBRO_ID_FIELD = "_cerebro_id"
_UUID5_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

_KEYWORD_PROPERTIES: frozenset[str] = frozenset(
    {"namespace", "repo", "source", "git_commit", "title", _CEREBRO_ID_FIELD}
)


def _to_weaviate_uuid(doc_id: str) -> str:
    """Map an arbitrary string document ID to a deterministic UUID string."""
    return str(uuid.uuid5(_UUID5_NAMESPACE, doc_id))


def _capitalize_collection(name: str) -> str:
    """Convert snake_case collection names to PascalCase for Weaviate class compatibility."""
    if not name:
        return name
    return "".join(part.capitalize() for part in name.split("_"))


class WeaviateVectorStoreProvider(VectorStoreProvider):
    """
    VectorStoreProvider backed by Weaviate.

    Supports local Weaviate (Docker / embedded) and Weaviate Cloud Service.
    Bring-your-own-vectors mode (no built-in vectorizer).

    Required environment variables (local deployment):
        WEAVIATE_URL   — HTTP URL, e.g. http://localhost:8080  (default)

    Optional:
        WEAVIATE_GRPC_PORT      — gRPC port for v4 client (default: 50051)
        WEAVIATE_API_KEY        — API key for WCS or secured clusters
        WEAVIATE_ENABLE_HYBRID  — "true" to enable BM25+vector hybrid queries
    """

    backend_name: ClassVar[str] = "weaviate"
    DEFAULT_URL: ClassVar[str] = "http://localhost:8080"
    DEFAULT_GRPC_PORT: ClassVar[int] = 50051
    DEFAULT_COLLECTION_NAME: ClassVar[str] = "cerebro_documents"
    DEFAULT_EMBEDDING_DIMENSIONS: ClassVar[int] = 384

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        grpc_port: int | None = None,
        collection_name: str | None = None,
        default_namespace: str | None = None,
        embedding_dimensions: int | None = None,
        enable_hybrid: bool = False,
    ) -> None:
        raw_url = url or os.getenv("WEAVIATE_URL", self.DEFAULT_URL).strip()
        parsed = urlparse(raw_url)
        self.http_host = parsed.hostname or "localhost"
        self.http_port = parsed.port or 8080
        self.http_secure = parsed.scheme == "https"

        raw_grpc = grpc_port or os.getenv("WEAVIATE_GRPC_PORT")
        self.grpc_port = int(raw_grpc) if raw_grpc else self.DEFAULT_GRPC_PORT
        self.grpc_secure = self.http_secure

        self.api_key = api_key or os.getenv("WEAVIATE_API_KEY")

        raw_name = collection_name or os.getenv(
            "WEAVIATE_COLLECTION_NAME", self.DEFAULT_COLLECTION_NAME
        )
        self.collection_name = _capitalize_collection(raw_name.strip())
        self.default_namespace = default_namespace
        self.embedding_dimensions = (
            embedding_dimensions
            if embedding_dimensions is not None
            else self.DEFAULT_EMBEDDING_DIMENSIONS
        )
        self.enable_hybrid = enable_hybrid or (
            os.getenv("WEAVIATE_ENABLE_HYBRID", "").lower() == "true"
        )

    # -------------------------------------------------------------------------
    # Schema bootstrap
    # -------------------------------------------------------------------------

    def initialize_schema(self, **kwargs) -> dict[str, Any]:
        """Create the Weaviate collection with COSINE HNSW if it does not exist."""

        try:
            from weaviate.classes.config import Configure, DataType, Property, VectorDistances
        except ImportError as exc:
            raise ImportError(
                "weaviate-client>=4.9 is required for the weaviate backend. "
                "Install with: pip install 'weaviate-client>=4.9'"
            ) from exc

        client = self._client()
        try:
            if client.collections.exists(self.collection_name):
                logger.info("Weaviate collection %r already exists.", self.collection_name)
                return {**self.get_backend_info(), "initialized": True}

            client.collections.create(
                name=self.collection_name,
                vectorizer_config=Configure.Vectorizer.none(),
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE,
                ),
                properties=[
                    Property(name="content", data_type=DataType.TEXT, skip_vectorization=True),
                    Property(name=_CEREBRO_ID_FIELD, data_type=DataType.TEXT,
                             skip_vectorization=True, index_filterable=True, index_searchable=False),
                    Property(name="namespace", data_type=DataType.TEXT,
                             skip_vectorization=True, index_filterable=True, index_searchable=False),
                    Property(name="source", data_type=DataType.TEXT,
                             skip_vectorization=True, index_filterable=True, index_searchable=False),
                    Property(name="title", data_type=DataType.TEXT,
                             skip_vectorization=True, index_filterable=True, index_searchable=True),
                    Property(name="repo", data_type=DataType.TEXT,
                             skip_vectorization=True, index_filterable=True, index_searchable=False),
                    Property(name="git_commit", data_type=DataType.TEXT,
                             skip_vectorization=True, index_filterable=True, index_searchable=False),
                ],
            )
            logger.info(
                "Weaviate collection %r created (dims=%s, distance=COSINE).",
                self.collection_name,
                self.embedding_dimensions,
            )
        finally:
            client.close()

        return {**self.get_backend_info(), "initialized": True}

    # -------------------------------------------------------------------------
    # Write
    # -------------------------------------------------------------------------

    def add_documents(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[list[float]],
        namespace: str | None = None,
        **kwargs,
    ) -> int:
        return self.upsert_documents(documents, embeddings, namespace=namespace, **kwargs)

    def upsert_documents(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[list[float]],
        namespace: str | None = None,
        **kwargs,
    ) -> int:
        if not documents:
            return 0
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Document count ({len(documents)}) must match embedding count ({len(embeddings)})."
            )

        try:
            from weaviate.classes.data import DataObject
        except ImportError as exc:
            raise ImportError("weaviate-client>=4.9 is required for the weaviate backend.") from exc

        resolved_namespace = namespace or self.default_namespace
        objects = [
            self._build_object(doc, emb, resolved_namespace, idx)
            for idx, (doc, emb) in enumerate(zip(documents, embeddings))
        ]

        client = self._client()
        try:
            collection = client.collections.get(self.collection_name)
            response = collection.data.insert_many(objects)
            if response.has_errors:
                for err in response.errors.values():
                    logger.warning("Weaviate upsert partial error: %s", err.message)
            return len(documents) - len(response.errors)
        finally:
            client.close()

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: MetadataFilters | None = None,
        namespace: str | None = None,
        min_score: float | None = None,
        **kwargs,
    ) -> list[VectorSearchResult]:
        if top_k <= 0:
            return []

        resolved_namespace = namespace or self.default_namespace
        weaviate_filter = self._build_filter(filters, resolved_namespace)
        query_text: str | None = kwargs.get("query_text")
        use_hybrid = self.enable_hybrid and bool(query_text)

        try:
            from weaviate.classes.query import MetadataQuery
        except ImportError as exc:
            raise ImportError("weaviate-client>=4.9 is required for the weaviate backend.") from exc

        client = self._client()
        try:
            collection = client.collections.get(self.collection_name)

            if use_hybrid:
                response = collection.query.hybrid(
                    query=query_text,
                    vector=query_embedding,
                    limit=top_k,
                    filters=weaviate_filter,
                    return_metadata=MetadataQuery(score=True),
                )
                raw_results = [
                    (obj, float(obj.metadata.score or 0.0))
                    for obj in response.objects
                ]
            else:
                response = collection.query.near_vector(
                    near_vector=query_embedding,
                    limit=top_k,
                    filters=weaviate_filter,
                    return_metadata=MetadataQuery(certainty=True, distance=True),
                    distance=None if min_score is None else (1.0 - min_score) * 2,
                )
                raw_results = []
                for obj in response.objects:
                    certainty = obj.metadata.certainty
                    if certainty is None and obj.metadata.distance is not None:
                        certainty = max(0.0, 1.0 - obj.metadata.distance / 2.0)
                    score = float(certainty or 0.0)
                    raw_results.append((obj, score))
        finally:
            client.close()

        results: list[VectorSearchResult] = []
        for obj, score in raw_results:
            if min_score is not None and score < min_score:
                continue
            props = dict(obj.properties)
            original_id = str(props.pop(_CEREBRO_ID_FIELD, str(obj.uuid)))
            content = str(props.pop("content", ""))
            results.append(
                VectorSearchResult(
                    id=original_id,
                    content=content,
                    metadata=props,
                    score=score,
                    namespace=props.get("namespace"),
                    title=props.get("title"),
                    source=props.get("source"),
                )
            )

        return results

    # -------------------------------------------------------------------------
    # Delete / clear
    # -------------------------------------------------------------------------

    def delete_documents(
        self,
        document_ids: list[str],
        namespace: str | None = None,
    ) -> int:
        if not document_ids:
            return 0

        try:
            from weaviate.classes.query import Filter
        except ImportError as exc:
            raise ImportError("weaviate-client>=4.9 is required for the weaviate backend.") from exc

        client = self._client()
        try:
            collection = client.collections.get(self.collection_name)
            response = collection.data.delete_many(
                where=Filter.by_property(_CEREBRO_ID_FIELD).contains_any(document_ids)
            )
            return int(response.successful)
        finally:
            client.close()

    def clear(self, namespace: str | None = None) -> None:
        resolved_namespace = namespace or self.default_namespace

        client = self._client()
        try:
            collection = client.collections.get(self.collection_name)
            if resolved_namespace:
                try:
                    from weaviate.classes.query import Filter
                except ImportError as exc:
                    raise ImportError(
                        "weaviate-client>=4.9 is required for the weaviate backend."
                    ) from exc
                collection.data.delete_many(
                    where=Filter.by_property("namespace").equal(resolved_namespace)
                )
            else:
                client.collections.delete(self.collection_name)
        finally:
            client.close()

        if not resolved_namespace:
            self.initialize_schema()

    # -------------------------------------------------------------------------
    # Counts / health
    # -------------------------------------------------------------------------

    def get_document_count(self, namespace: str | None = None) -> int:
        resolved_namespace = namespace or self.default_namespace

        client = self._client()
        try:
            collection = client.collections.get(self.collection_name)
            if resolved_namespace:
                try:
                    from weaviate.classes.query import Filter
                except ImportError:
                    pass
                else:
                    aggregate = collection.aggregate.over_all(
                        filters=Filter.by_property("namespace").equal(resolved_namespace),
                        total_count=True,
                    )
                    return int(aggregate.total_count or 0)
            aggregate = collection.aggregate.over_all(total_count=True)
            return int(aggregate.total_count or 0)
        finally:
            client.close()

    def health_check(self) -> bool:
        try:
            client = self._client()
            try:
                ready = client.is_ready()
            finally:
                client.close()
            return ready
        except Exception as exc:
            logger.warning("Weaviate health check failed: %s", exc)
            return False

    def get_backend_info(self) -> dict[str, Any]:
        return {
            "backend": self.backend_name,
            "http_host": self.http_host,
            "http_port": self.http_port,
            "collection_name": self.collection_name,
            "default_namespace": self.default_namespace,
            "embedding_dimensions": self.embedding_dimensions,
            "enable_hybrid": self.enable_hybrid,
            "supports_filters": True,
            "supports_namespace": True,
            "supports_hybrid": True,
            "production_ready": True,
        }

    # -------------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------------

    def export_documents(
        self,
        namespace: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[StoredVectorDocument]:
        """Export documents with embeddings for backend migration."""

        resolved_namespace = namespace or self.default_namespace

        try:
            from weaviate.classes.query import Filter
        except ImportError as exc:
            raise ImportError("weaviate-client>=4.9 is required for the weaviate backend.") from exc

        weaviate_filter = (
            Filter.by_property("namespace").equal(resolved_namespace)
            if resolved_namespace
            else None
        )

        client = self._client()
        try:
            collection = client.collections.get(self.collection_name)
            response = collection.query.fetch_objects(
                limit=limit,
                offset=offset,
                filters=weaviate_filter,
                include_vector=True,
            )
        finally:
            client.close()

        exported: list[StoredVectorDocument] = []
        for obj in response.objects:
            props = dict(obj.properties)
            original_id = str(props.pop(_CEREBRO_ID_FIELD, str(obj.uuid)))
            content = str(props.pop("content", ""))
            vector = obj.vector.get("default", []) if isinstance(obj.vector, dict) else (obj.vector or [])

            exported.append(
                StoredVectorDocument(
                    id=original_id,
                    content=content,
                    metadata=props,
                    embedding=[float(v) for v in vector],
                    namespace=props.get("namespace"),
                    title=props.get("title"),
                    source=props.get("source"),
                )
            )

        return exported

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _build_object(
        self,
        document: dict[str, Any],
        embedding: list[float],
        namespace: str | None,
        index: int,
    ):
        try:
            from weaviate.classes.data import DataObject
        except ImportError as exc:
            raise ImportError("weaviate-client>=4.9 is required for the weaviate backend.") from exc

        import json

        doc_id = str(document.get("id", f"doc_{index}"))
        resolved_namespace = (
            document.get("namespace")
            if isinstance(document.get("namespace"), str) and document["namespace"].strip()
            else namespace
        )

        properties: dict[str, Any] = {
            _CEREBRO_ID_FIELD: doc_id,
            "content": str(document.get("content", document.get("text", ""))),
        }

        for key, value in document.items():
            if key in {"id", "content", "text"}:
                continue
            if key in _KEYWORD_PROPERTIES:
                properties[key] = str(value) if value is not None else None
            elif isinstance(value, (str, int, float, bool)) or value is None:
                properties[key] = value
            else:
                properties[key] = json.dumps(value, ensure_ascii=True)

        if resolved_namespace:
            properties["namespace"] = resolved_namespace

        return DataObject(
            properties=properties,
            vector=embedding,
            uuid=_to_weaviate_uuid(doc_id),
        )

    def _build_filter(
        self,
        filters: MetadataFilters | None,
        namespace: str | None,
    ):
        try:
            from weaviate.classes.query import Filter
        except ImportError:
            return None

        conditions = []

        if namespace:
            conditions.append(Filter.by_property("namespace").equal(namespace))

        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                conditions.append(Filter.by_property(key).equal(value))

        if not conditions:
            return None

        combined = conditions[0]
        for c in conditions[1:]:
            combined = combined & c
        return combined

    def _client(self):
        try:
            import weaviate
        except ImportError as exc:
            raise ImportError(
                "weaviate-client>=4.9 is required for the weaviate backend. "
                "Install with: pip install 'weaviate-client>=4.9'"
            ) from exc

        if self.api_key:
            auth = weaviate.auth.AuthApiKey(self.api_key)
        else:
            auth = None

        return weaviate.connect_to_custom(
            http_host=self.http_host,
            http_port=self.http_port,
            http_secure=self.http_secure,
            grpc_host=self.http_host,
            grpc_port=self.grpc_port,
            grpc_secure=self.grpc_secure,
            auth_credentials=auth,
        )
