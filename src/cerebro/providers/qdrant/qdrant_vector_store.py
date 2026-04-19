"""
Qdrant Vector Store Provider

Production vector store backed by Qdrant.
Requires the `qdrant-client` package.

Namespace isolation is implemented via a filterable `namespace` payload field.
String document IDs are mapped to deterministic UUIDs (UUID5) because Qdrant
point IDs must be uint64 or UUID. The original string ID is always preserved in
the payload under `_cerebro_id` so round-trips are lossless.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, ClassVar

from cerebro.interfaces.vector_store import (
    MetadataFilters,
    StoredVectorDocument,
    VectorSearchResult,
    VectorStoreProvider,
)

logger = logging.getLogger("cerebro.providers.qdrant")

_CEREBRO_ID_FIELD = "_cerebro_id"
_UUID5_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _to_point_id(doc_id: str) -> str:
    """Map an arbitrary string document ID to a deterministic UUID string."""
    return str(uuid.uuid5(_UUID5_NAMESPACE, doc_id))


class QdrantVectorStoreProvider(VectorStoreProvider):
    """
    VectorStoreProvider backed by Qdrant.

    Required environment variables:
        QDRANT_URL      — Qdrant server URL (default: http://localhost:6333)

    Optional:
        QDRANT_API_KEY  — API key for Qdrant Cloud or secured clusters
    """

    backend_name: ClassVar[str] = "qdrant"
    DEFAULT_COLLECTION_NAME: ClassVar[str] = "cerebro_documents"
    DEFAULT_URL: ClassVar[str] = "http://localhost:6333"
    DEFAULT_EMBEDDING_DIMENSIONS: ClassVar[int] = 384

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        collection_name: str | None = None,
        default_namespace: str | None = None,
        embedding_dimensions: int | None = None,
    ) -> None:
        self.url = url or os.getenv("QDRANT_URL", self.DEFAULT_URL).strip()
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        self.collection_name = (
            collection_name
            or os.getenv("QDRANT_COLLECTION_NAME", self.DEFAULT_COLLECTION_NAME).strip()
        )
        self.default_namespace = default_namespace
        self.embedding_dimensions = (
            embedding_dimensions
            if embedding_dimensions is not None
            else self.DEFAULT_EMBEDDING_DIMENSIONS
        )

    # -------------------------------------------------------------------------
    # Schema bootstrap
    # -------------------------------------------------------------------------

    def initialize_schema(self, **kwargs) -> dict[str, Any]:
        """Create the Qdrant collection with COSINE distance if it does not exist."""

        try:
            from qdrant_client.http.models import Distance, VectorParams
        except ImportError as exc:
            raise ImportError(
                "qdrant-client is required for the qdrant backend. "
                "Install with: pip install 'qdrant-client>=1.9'"
            ) from exc

        client = self._client()

        try:
            info = client.get_collection(self.collection_name)
            logger.info(
                "Qdrant collection %r already exists (%s points).",
                self.collection_name,
                info.points_count,
            )
        except Exception:
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimensions,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(
                "Qdrant collection %r created (dims=%s, distance=COSINE).",
                self.collection_name,
                self.embedding_dimensions,
            )

        return {
            **self.get_backend_info(),
            "initialized": True,
        }

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
            from qdrant_client.http.models import PointStruct
        except ImportError as exc:
            raise ImportError(
                "qdrant-client is required for the qdrant backend."
            ) from exc

        resolved_namespace = namespace or self.default_namespace
        points = [
            self._build_point(doc, emb, resolved_namespace, idx)
            for idx, (doc, emb) in enumerate(zip(documents, embeddings))
        ]

        client = self._client()
        client.upsert(collection_name=self.collection_name, points=points)
        return len(points)

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
        query_filter = self._build_filter(filters, resolved_namespace)

        client = self._client()
        hits = client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
            score_threshold=min_score,
        )

        results: list[VectorSearchResult] = []
        for hit in hits:
            payload = hit.payload or {}
            original_id = payload.pop(_CEREBRO_ID_FIELD, str(hit.id))
            results.append(
                VectorSearchResult(
                    id=original_id,
                    content=str(payload.pop("content", "")),
                    metadata=payload,
                    score=float(hit.score),
                    namespace=payload.get("namespace"),
                    title=payload.get("title"),
                    source=payload.get("source"),
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
            from qdrant_client.http.models import PointIdsList
        except ImportError as exc:
            raise ImportError(
                "qdrant-client is required for the qdrant backend."
            ) from exc

        point_ids = [_to_point_id(doc_id) for doc_id in document_ids]
        client = self._client()
        client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=point_ids),
        )
        return len(document_ids)

    def clear(self, namespace: str | None = None) -> None:
        """
        Delete all points, optionally scoped to a namespace.

        When no namespace is given the entire collection is dropped and
        recreated to guarantee a clean state.
        """
        resolved_namespace = namespace or self.default_namespace

        if resolved_namespace:
            try:
                from qdrant_client.http.models import FieldCondition, Filter, MatchValue
            except ImportError as exc:
                raise ImportError(
                    "qdrant-client is required for the qdrant backend."
                ) from exc

            client = self._client()
            client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="namespace",
                            match=MatchValue(value=resolved_namespace),
                        )
                    ]
                ),
            )
        else:
            client = self._client()
            client.delete_collection(self.collection_name)
            self.initialize_schema()

    # -------------------------------------------------------------------------
    # Counts / health
    # -------------------------------------------------------------------------

    def get_document_count(self, namespace: str | None = None) -> int:
        resolved_namespace = namespace or self.default_namespace
        query_filter = self._build_filter(None, resolved_namespace)

        client = self._client()
        result = client.count(
            collection_name=self.collection_name,
            count_filter=query_filter,
            exact=True,
        )
        return int(result.count)

    def health_check(self) -> bool:
        try:
            self._client().get_collection(self.collection_name)
            return True
        except Exception as exc:
            logger.warning("Qdrant health check failed: %s", exc)
            return False

    def get_backend_info(self) -> dict[str, Any]:
        return {
            "backend": self.backend_name,
            "url": self.url,
            "collection_name": self.collection_name,
            "default_namespace": self.default_namespace,
            "embedding_dimensions": self.embedding_dimensions,
            "supports_filters": True,
            "supports_namespace": True,
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
        query_filter = self._build_filter(None, resolved_namespace)

        client = self._client()
        records, _ = client.scroll(
            collection_name=self.collection_name,
            scroll_filter=query_filter,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )

        exported: list[StoredVectorDocument] = []
        for record in records:
            payload = dict(record.payload or {})
            original_id = payload.pop(_CEREBRO_ID_FIELD, str(record.id))
            content = str(payload.pop("content", ""))
            vector = record.vector or []

            exported.append(
                StoredVectorDocument(
                    id=original_id,
                    content=content,
                    metadata=payload,
                    embedding=[float(v) for v in vector],
                    namespace=payload.get("namespace"),
                    title=payload.get("title"),
                    source=payload.get("source"),
                )
            )

        return exported

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _build_point(
        self,
        document: dict[str, Any],
        embedding: list[float],
        namespace: str | None,
        index: int,
    ):
        try:
            from qdrant_client.http.models import PointStruct
        except ImportError as exc:
            raise ImportError("qdrant-client is required for the qdrant backend.") from exc

        doc_id = str(document.get("id", f"doc_{index}"))
        resolved_namespace = (
            document.get("namespace")
            if isinstance(document.get("namespace"), str) and document["namespace"].strip()
            else namespace
        )

        payload: dict[str, Any] = {
            _CEREBRO_ID_FIELD: doc_id,
            "content": str(document.get("content", document.get("text", ""))),
        }

        for key, value in document.items():
            if key in {"id", "content", "text"}:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                payload[key] = value
            else:
                import json
                payload[key] = json.dumps(value, ensure_ascii=True)

        if resolved_namespace:
            payload["namespace"] = resolved_namespace

        return PointStruct(
            id=_to_point_id(doc_id),
            vector=embedding,
            payload=payload,
        )

    def _build_filter(
        self,
        filters: MetadataFilters | None,
        namespace: str | None,
    ):
        try:
            from qdrant_client.http.models import FieldCondition, Filter, MatchValue
        except ImportError:
            return None

        conditions = []

        if namespace:
            conditions.append(
                FieldCondition(key="namespace", match=MatchValue(value=namespace))
            )

        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )

        if not conditions:
            return None

        return Filter(must=conditions)

    def _client(self):
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise ImportError(
                "qdrant-client is required for the qdrant backend. "
                "Install with: pip install 'qdrant-client>=1.9'"
            ) from exc

        kwargs: dict[str, Any] = {"url": self.url}
        if self.api_key:
            kwargs["api_key"] = self.api_key

        return QdrantClient(**kwargs)
