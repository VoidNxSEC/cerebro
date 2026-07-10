"""
Azure AI Search Vector Store Provider

Production vector store backed by Azure AI Search (formerly Cognitive Search).
Requires the `azure-search-documents` package.

Namespace isolation is implemented via a filterable `namespace` field.
Metadata filters are supported for the predefined filterable fields listed in
_FILTERABLE_METADATA_FIELDS. Arbitrary metadata keys are stored in
`metadata_json` but cannot be used as OData filters.

Azure AI Search does not expose stored vectors through the search API, so
export_documents() returns documents with empty embeddings (content-only
migration is still possible).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, ClassVar

from cerebro.interfaces.vector_store import (
    MetadataFilters,
    StoredVectorDocument,
    VectorSearchResult,
    VectorStoreProvider,
)

logger = logging.getLogger("cerebro.providers.azure_search")

_FILTERABLE_METADATA_FIELDS: frozenset[str] = frozenset(
    {"namespace", "repo", "source", "git_commit"}
)


class AzureSearchVectorStoreProvider(VectorStoreProvider):
    """
    VectorStoreProvider backed by Azure AI Search.

    Required environment variables:
        AZURE_SEARCH_API_KEY          — service admin or query key
        AZURE_SEARCH_ENDPOINT         — https://<name>.search.windows.net
          OR
        AZURE_SEARCH_SERVICE_NAME     — <name> (endpoint is derived automatically)

    Optional:
        AZURE_SEARCH_INDEX_NAME       — defaults to "cerebro-documents"
    """

    backend_name: ClassVar[str] = "azure_search"
    DEFAULT_INDEX_NAME: ClassVar[str] = "cerebro-documents"
    DEFAULT_EMBEDDING_DIMENSIONS: ClassVar[int] = 384
    _VECTOR_FIELD: ClassVar[str] = "content_vector"
    _KEY_FIELD: ClassVar[str] = "id"

    def __init__(
        self,
        service_endpoint: str | None = None,
        index_name: str | None = None,
        api_key: str | None = None,
        default_namespace: str | None = None,
        embedding_dimensions: int | None = None,
    ) -> None:
        self.service_endpoint = (
            service_endpoint
            or os.getenv("AZURE_SEARCH_ENDPOINT")
            or self._endpoint_from_service_name()
        )
        self.index_name = (
            index_name
            or os.getenv("AZURE_SEARCH_INDEX_NAME", self.DEFAULT_INDEX_NAME).strip()
        )
        self.api_key = api_key or os.getenv("AZURE_SEARCH_API_KEY")
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
        """Create or update the Azure AI Search index with HNSW vector search."""

        index_client = self._index_client()
        index_def = self._build_index_definition()

        try:
            index_client.get_index(self.index_name)
            index_client.create_or_update_index(index_def)
            logger.info("Azure Search index %r updated.", self.index_name)
        except Exception:
            index_client.create_index(index_def)
            logger.info("Azure Search index %r created.", self.index_name)

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

        resolved_namespace = namespace or self.default_namespace
        client = self._search_client()
        batch = [
            self._build_document(doc, emb, resolved_namespace, idx)
            for idx, (doc, emb) in enumerate(zip(documents, embeddings))
        ]

        result = client.upload_documents(batch)
        succeeded = sum(1 for r in result if r.succeeded)
        if succeeded < len(batch):
            logger.warning(
                "Azure Search upsert: %d/%d documents succeeded.",
                succeeded,
                len(batch),
            )
        return succeeded

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

        try:
            from azure.search.documents.models import VectorizedQuery
        except ImportError as exc:
            raise ImportError(
                "azure-search-documents is required for the azure_search backend."
            ) from exc

        resolved_namespace = namespace or self.default_namespace
        odata_filter = self._build_odata_filter(filters, resolved_namespace)

        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top_k,
            fields=self._VECTOR_FIELD,
        )

        client = self._search_client()
        raw_results = client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=odata_filter,
            top=top_k,
            select=[
                "id",
                "content",
                "namespace",
                "title",
                "source",
                "repo",
                "git_commit",
                "metadata_json",
            ],
        )

        results: list[VectorSearchResult] = []
        for hit in raw_results:
            score = float(hit.get("@search.score", 0.0))
            if min_score is not None and score < min_score:
                continue

            metadata = self._decode_metadata_json(hit.get("metadata_json"))
            for field in _FILTERABLE_METADATA_FIELDS:
                if hit.get(field) is not None:
                    metadata.setdefault(field, hit[field])

            results.append(
                VectorSearchResult(
                    id=str(hit.get("id", "")),
                    content=str(hit.get("content", "")),
                    metadata=metadata,
                    score=score,
                    namespace=hit.get("namespace"),
                    title=hit.get("title") or metadata.get("title"),
                    source=hit.get("source") or metadata.get("source"),
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

        client = self._search_client()
        batch = [{self._KEY_FIELD: doc_id} for doc_id in document_ids]
        result = client.delete_documents(batch)
        return sum(1 for r in result if r.succeeded)

    def clear(self, namespace: str | None = None) -> None:
        """
        Delete all documents, optionally scoped to a namespace.

        Azure AI Search has no bulk-delete API; this paginates over all
        matching documents and deletes them in batches of 1000.
        """
        resolved_namespace = namespace or self.default_namespace
        odata_filter = None
        if resolved_namespace:
            odata_filter = f"namespace eq '{self._escape_odata_string(resolved_namespace)}'"

        client = self._search_client()
        batch: list[dict[str, str]] = []

        for doc in client.search(search_text="*", filter=odata_filter, select=["id"], top=1000):
            batch.append({self._KEY_FIELD: doc["id"]})
            if len(batch) >= 1000:
                client.delete_documents(batch)
                batch = []

        if batch:
            client.delete_documents(batch)

    # -------------------------------------------------------------------------
    # Counts / health
    # -------------------------------------------------------------------------

    def get_document_count(self, namespace: str | None = None) -> int:
        resolved_namespace = namespace or self.default_namespace
        odata_filter = None
        if resolved_namespace:
            odata_filter = f"namespace eq '{self._escape_odata_string(resolved_namespace)}'"

        client = self._search_client()
        results = client.search(
            search_text="*",
            filter=odata_filter,
            include_total_count=True,
            top=0,
        )
        return int(results.get_count() or 0)

    def health_check(self) -> bool:
        if not self.service_endpoint or not self.api_key:
            return False

        try:
            self._index_client().get_index(self.index_name)
            return True
        except Exception as exc:
            logger.warning("Azure Search health check failed: %s", exc)
            return False

    def get_backend_info(self) -> dict[str, Any]:
        return {
            "backend": self.backend_name,
            "index_name": self.index_name,
            "service_endpoint": self.service_endpoint,
            "default_namespace": self.default_namespace,
            "embedding_dimensions": self.embedding_dimensions,
            "supports_filters": True,
            "supports_namespace": True,
            "filterable_fields": sorted(_FILTERABLE_METADATA_FIELDS),
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
        """
        Export documents for content-only backend migration.

        Azure AI Search does not return stored vectors through the search API.
        Exported documents carry empty embeddings; re-embed them before
        importing into a new backend.
        """
        resolved_namespace = namespace or self.default_namespace
        odata_filter = None
        if resolved_namespace:
            odata_filter = f"namespace eq '{self._escape_odata_string(resolved_namespace)}'"

        client = self._search_client()
        raw_results = client.search(
            search_text="*",
            filter=odata_filter,
            select=[
                "id",
                "content",
                "namespace",
                "title",
                "source",
                "repo",
                "git_commit",
                "metadata_json",
            ],
            top=limit,
            skip=offset,
        )

        exported: list[StoredVectorDocument] = []
        for hit in raw_results:
            metadata = self._decode_metadata_json(hit.get("metadata_json"))
            for field in _FILTERABLE_METADATA_FIELDS:
                if hit.get(field) is not None:
                    metadata.setdefault(field, hit[field])

            exported.append(
                StoredVectorDocument(
                    id=str(hit.get("id", "")),
                    content=str(hit.get("content", "")),
                    metadata=metadata,
                    embedding=[],
                    namespace=hit.get("namespace"),
                    title=hit.get("title") or metadata.get("title"),
                    source=hit.get("source") or metadata.get("source"),
                )
            )

        return exported

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _build_document(
        self,
        document: dict[str, Any],
        embedding: list[float],
        namespace: str | None,
        index: int,
    ) -> dict[str, Any]:
        resolved_namespace = (
            document.get("namespace")
            if isinstance(document.get("namespace"), str)
            and document["namespace"].strip()
            else namespace
        )

        filterable = {
            field: str(document[field])
            for field in _FILTERABLE_METADATA_FIELDS
            if field in document and document[field] is not None
        }
        if resolved_namespace:
            filterable["namespace"] = str(resolved_namespace)

        remaining_metadata = {
            key: value
            for key, value in document.items()
            if key
            not in {"id", "content", "text", "title", "source"}
            | _FILTERABLE_METADATA_FIELDS
        }

        return {
            "id": str(document.get("id", f"doc_{index}")),
            "content": str(document.get("content", document.get("text", ""))),
            "title": str(document.get("title", "")),
            "source": str(document.get("source", "")),
            "metadata_json": json.dumps(
                remaining_metadata, ensure_ascii=True, sort_keys=True
            ),
            self._VECTOR_FIELD: embedding,
            **filterable,
        }

    def _build_index_definition(self):
        try:
            from azure.search.documents.indexes.models import (
                HnswAlgorithmConfiguration,
                SearchField,
                SearchFieldDataType,
                SearchIndex,
                SimpleField,
                VectorSearch,
                VectorSearchProfile,
            )
        except ImportError as exc:
            raise ImportError(
                "azure-search-documents is required for the azure_search backend."
            ) from exc

        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="cerebro-hnsw")],
            profiles=[
                VectorSearchProfile(
                    name="cerebro-vector-profile",
                    algorithm_configuration_name="cerebro-hnsw",
                )
            ],
        )

        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
            SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
            SearchField(
                name="title",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
            ),
            SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
            SimpleField(
                name="namespace",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
            ),
            SimpleField(name="repo", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="git_commit", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="metadata_json", type=SearchFieldDataType.String),
            SearchField(
                name=self._VECTOR_FIELD,
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=self.embedding_dimensions,
                vector_search_profile_name="cerebro-vector-profile",
            ),
        ]

        return SearchIndex(name=self.index_name, fields=fields, vector_search=vector_search)

    def _build_odata_filter(
        self,
        filters: MetadataFilters | None,
        namespace: str | None,
    ) -> str | None:
        clauses: list[str] = []

        if namespace:
            clauses.append(f"namespace eq '{self._escape_odata_string(namespace)}'")

        if filters:
            supported = _FILTERABLE_METADATA_FIELDS | {"title", "source"}
            for key, value in filters.items():
                if value is None:
                    continue
                if key not in supported:
                    logger.debug(
                        "Filter key %r is not a top-level filterable field in Azure Search; skipping.",
                        key,
                    )
                    continue
                clauses.append(f"{key} eq '{self._escape_odata_string(str(value))}'")

        return " and ".join(clauses) if clauses else None

    def _search_client(self):
        try:
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents import SearchClient
        except ImportError as exc:
            raise ImportError(
                "azure-search-documents is required for the azure_search backend. "
                "Install with: pip install 'azure-search-documents>=11.4' azure-core"
            ) from exc

        if not self.service_endpoint:
            raise ValueError(
                "Azure Search endpoint is not configured. "
                "Set AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_SERVICE_NAME."
            )
        if not self.api_key:
            raise ValueError(
                "AZURE_SEARCH_API_KEY must be configured for the azure_search backend."
            )

        return SearchClient(
            endpoint=self.service_endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.api_key),
        )

    def _index_client(self):
        try:
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents.indexes import SearchIndexClient
        except ImportError as exc:
            raise ImportError(
                "azure-search-documents is required for the azure_search backend."
            ) from exc

        if not self.service_endpoint:
            raise ValueError(
                "Azure Search endpoint is not configured. "
                "Set AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_SERVICE_NAME."
            )
        if not self.api_key:
            raise ValueError(
                "AZURE_SEARCH_API_KEY must be configured for the azure_search backend."
            )

        return SearchIndexClient(
            endpoint=self.service_endpoint,
            credential=AzureKeyCredential(self.api_key),
        )

    @staticmethod
    def _endpoint_from_service_name() -> str | None:
        name = os.getenv("AZURE_SEARCH_SERVICE_NAME", "").strip()
        return f"https://{name}.search.windows.net" if name else None

    @staticmethod
    def _escape_odata_string(value: str) -> str:
        return value.replace("'", "''")

    @staticmethod
    def _decode_metadata_json(raw: str | None) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
