"""
OpenSearch Vector Store Provider

Production vector store backed by OpenSearch using the k-NN plugin.
Requires the `opensearch-py` package.

Index strategy
--------------
Documents are stored in an OpenSearch index with a `knn_vector` field
(HNSW, cosinesimil space). Namespace isolation is implemented via a
`keyword` field that is always included in the bool filter clause.
Metadata fields listed in _KEYWORD_FIELDS are indexed as `keyword` for
exact-match filtering; all remaining metadata is packed into `metadata_json`
as a non-indexed string.

Score normalisation
-------------------
OpenSearch cosinesimil scores are in [0, 2]:
    raw_score = 1 + cosine(A, B)
We normalise to [0, 1] by dividing by 2 before returning results.
`min_score` is therefore expected in the [0, 1] range; it is scaled to the
raw threshold (min_score * 2) and passed to OpenSearch's `min_score` filter.

Hybrid search
-------------
When `query_text` is passed through **kwargs, the search falls back to a
bool/should query that combines the k-NN clause with a BM25 `match` on the
`content` field. This requires no additional setup but the score
normalisation changes: the combined score is no longer purely cosinesimil,
so it is clamped to [0, 1] using the configured or inferred max.

Elasticsearch 8.x compatibility
--------------------------------
Elasticsearch 8.x uses `dense_vector` instead of `knn_vector` and a
different search DSL. This provider is OpenSearch-native. For Elasticsearch,
set `es_compat=True` — this switches the field type and search format
automatically, relying on the same `opensearch-py` SDK.
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

logger = logging.getLogger("cerebro.providers.opensearch")

_KEYWORD_FIELDS: frozenset[str] = frozenset(
    {"namespace", "repo", "source", "git_commit", "title"}
)
_VECTOR_FIELD = "content_vector"
_CONTENT_FIELD = "content"
_METADATA_JSON_FIELD = "metadata_json"


class OpenSearchVectorStoreProvider(VectorStoreProvider):
    """
    VectorStoreProvider backed by OpenSearch (k-NN plugin required).

    Required environment variables:
        OPENSEARCH_URL      — cluster URL (default: http://localhost:9200)

    Optional:
        OPENSEARCH_USERNAME / OPENSEARCH_PASSWORD  — HTTP basic auth
        OPENSEARCH_API_KEY                         — API key auth
        OPENSEARCH_INDEX_NAME                      — index name (default: cerebro-documents)
        OPENSEARCH_ES_COMPAT                       — set to "true" for Elasticsearch 8.x
    """

    backend_name: ClassVar[str] = "opensearch"
    DEFAULT_INDEX_NAME: ClassVar[str] = "cerebro-documents"
    DEFAULT_URL: ClassVar[str] = "http://localhost:9200"
    DEFAULT_EMBEDDING_DIMENSIONS: ClassVar[int] = 384

    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        api_key: str | None = None,
        index_name: str | None = None,
        default_namespace: str | None = None,
        embedding_dimensions: int | None = None,
        enable_hybrid_search: bool = False,
        es_compat: bool = False,
    ) -> None:
        self.url = url or os.getenv("OPENSEARCH_URL", self.DEFAULT_URL).strip()
        self.username = username or os.getenv("OPENSEARCH_USERNAME")
        self.password = password or os.getenv("OPENSEARCH_PASSWORD")
        self.api_key = api_key or os.getenv("OPENSEARCH_API_KEY")
        self.index_name = (
            index_name
            or os.getenv("OPENSEARCH_INDEX_NAME", self.DEFAULT_INDEX_NAME).strip()
        )
        self.default_namespace = default_namespace
        self.embedding_dimensions = (
            embedding_dimensions
            if embedding_dimensions is not None
            else self.DEFAULT_EMBEDDING_DIMENSIONS
        )
        self.enable_hybrid_search = enable_hybrid_search
        self.es_compat = es_compat or os.getenv("OPENSEARCH_ES_COMPAT", "").lower() == "true"

    # -------------------------------------------------------------------------
    # Schema bootstrap
    # -------------------------------------------------------------------------

    def initialize_schema(self, **kwargs) -> dict[str, Any]:
        """Create the OpenSearch index with k-NN vector mapping if absent."""

        client = self._client()

        if client.indices.exists(index=self.index_name):
            logger.info("OpenSearch index %r already exists.", self.index_name)
            return {**self.get_backend_info(), "initialized": False, "already_existed": True}

        mapping = self._build_index_mapping()
        client.indices.create(index=self.index_name, body=mapping)
        logger.info(
            "OpenSearch index %r created (dims=%s, es_compat=%s).",
            self.index_name,
            self.embedding_dimensions,
            self.es_compat,
        )
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

        resolved_namespace = namespace or self.default_namespace
        bulk_lines: list[str] = []

        for idx, (doc, emb) in enumerate(zip(documents, embeddings)):
            doc_id = str(doc.get("id", f"doc_{idx}"))
            body = self._build_doc_body(doc, emb, resolved_namespace)
            # _op_type index overwrites existing documents (idempotent upsert)
            bulk_lines.append(
                json.dumps({"index": {"_index": self.index_name, "_id": doc_id}})
            )
            bulk_lines.append(json.dumps(body))

        bulk_body = "\n".join(bulk_lines) + "\n"
        response = self._client().bulk(body=bulk_body, index=self.index_name, refresh=True)

        errors = [item for item in response.get("items", []) if "error" in item.get("index", {})]
        if errors:
            logger.warning(
                "OpenSearch bulk upsert: %d/%d documents failed.",
                len(errors),
                len(documents),
            )

        return len(documents) - len(errors)

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
        filter_clauses = self._build_filter_clauses(filters, resolved_namespace)
        query_text: str | None = kwargs.get("query_text")

        query_body = self._build_search_query(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_clauses=filter_clauses,
            query_text=query_text if self.enable_hybrid_search else None,
        )

        if min_score is not None:
            # Scale [0,1] threshold to raw OpenSearch cosinesimil range [0,2]
            query_body["min_score"] = min_score * 2

        query_body["size"] = top_k

        response = self._client().search(index=self.index_name, body=query_body)
        hits = response.get("hits", {}).get("hits", [])

        results: list[VectorSearchResult] = []
        for hit in hits:
            raw_score = float(hit.get("_score", 0.0))
            # Normalise cosinesimil score from [0,2] to [0,1]
            normalized_score = min(raw_score / 2.0, 1.0)

            source = hit.get("_source", {})
            metadata = self._decode_metadata_json(source.get(_METADATA_JSON_FIELD))
            for field in _KEYWORD_FIELDS:
                if source.get(field) is not None:
                    metadata.setdefault(field, source[field])

            results.append(
                VectorSearchResult(
                    id=str(hit.get("_id", "")),
                    content=str(source.get(_CONTENT_FIELD, "")),
                    metadata=metadata,
                    score=normalized_score,
                    namespace=source.get("namespace"),
                    title=source.get("title") or metadata.get("title"),
                    source=source.get("source") or metadata.get("source"),
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

        bulk_lines: list[str] = []
        for doc_id in document_ids:
            bulk_lines.append(
                json.dumps({"delete": {"_index": self.index_name, "_id": doc_id}})
            )

        bulk_body = "\n".join(bulk_lines) + "\n"
        response = self._client().bulk(body=bulk_body, refresh=True)
        deleted = sum(
            1
            for item in response.get("items", [])
            if item.get("delete", {}).get("result") == "deleted"
        )
        return deleted

    def clear(self, namespace: str | None = None) -> None:
        """Delete all documents, optionally scoped to a namespace.

        Without a namespace, deletes the entire index and recreates it.
        """
        resolved_namespace = namespace or self.default_namespace
        client = self._client()

        if resolved_namespace:
            client.delete_by_query(
                index=self.index_name,
                body={"query": {"term": {"namespace": resolved_namespace}}},
                refresh=True,
            )
        else:
            if client.indices.exists(index=self.index_name):
                client.indices.delete(index=self.index_name)
            self.initialize_schema()

    # -------------------------------------------------------------------------
    # Counts / health
    # -------------------------------------------------------------------------

    def get_document_count(self, namespace: str | None = None) -> int:
        resolved_namespace = namespace or self.default_namespace
        client = self._client()

        if resolved_namespace:
            body = {"query": {"term": {"namespace": resolved_namespace}}}
        else:
            body = {"query": {"match_all": {}}}

        response = client.count(index=self.index_name, body=body)
        return int(response.get("count", 0))

    def health_check(self) -> bool:
        try:
            self._client().cluster.health(index=self.index_name)
            return True
        except Exception as exc:
            logger.warning("OpenSearch health check failed: %s", exc)
            return False

    def get_backend_info(self) -> dict[str, Any]:
        return {
            "backend": self.backend_name,
            "url": self.url,
            "index_name": self.index_name,
            "default_namespace": self.default_namespace,
            "embedding_dimensions": self.embedding_dimensions,
            "enable_hybrid_search": self.enable_hybrid_search,
            "es_compat": self.es_compat,
            "supports_filters": True,
            "supports_namespace": True,
            "filterable_fields": sorted(_KEYWORD_FIELDS),
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
        """Export documents with embeddings using the scroll API."""

        resolved_namespace = namespace or self.default_namespace
        client = self._client()

        if resolved_namespace:
            query_body: dict[str, Any] = {
                "query": {"term": {"namespace": resolved_namespace}},
                "_source": True,
            }
        else:
            query_body = {"query": {"match_all": {}}, "_source": True}

        response = client.search(
            index=self.index_name,
            body=query_body,
            size=limit,
            from_=offset,
        )
        hits = response.get("hits", {}).get("hits", [])

        exported: list[StoredVectorDocument] = []
        for hit in hits:
            source = hit.get("_source", {})
            metadata = self._decode_metadata_json(source.get(_METADATA_JSON_FIELD))
            for field in _KEYWORD_FIELDS:
                if source.get(field) is not None:
                    metadata.setdefault(field, source[field])

            raw_vector = source.get(_VECTOR_FIELD, [])
            exported.append(
                StoredVectorDocument(
                    id=str(hit.get("_id", "")),
                    content=str(source.get(_CONTENT_FIELD, "")),
                    metadata=metadata,
                    embedding=[float(v) for v in raw_vector],
                    namespace=source.get("namespace"),
                    title=source.get("title") or metadata.get("title"),
                    source=source.get("source") or metadata.get("source"),
                )
            )

        return exported

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _build_index_mapping(self) -> dict[str, Any]:
        """Build the index settings and mappings dict."""

        keyword_props = {field: {"type": "keyword"} for field in _KEYWORD_FIELDS}
        keyword_props[_METADATA_JSON_FIELD] = {"type": "keyword", "index": False}
        keyword_props[_CONTENT_FIELD] = {"type": "text", "analyzer": "english"}

        if self.es_compat:
            # Elasticsearch 8.x uses dense_vector with index + knn
            vector_prop: dict[str, Any] = {
                "type": "dense_vector",
                "dims": self.embedding_dimensions,
                "index": True,
                "similarity": "cosine",
            }
            settings: dict[str, Any] = {}
        else:
            # OpenSearch: knn_vector with HNSW method
            vector_prop = {
                "type": "knn_vector",
                "dimension": self.embedding_dimensions,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "nmslib",
                    "parameters": {"ef_construction": 128, "m": 16},
                },
            }
            settings = {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100,
                    "number_of_replicas": 0,
                }
            }

        return {
            "settings": settings,
            "mappings": {
                "properties": {
                    _VECTOR_FIELD: vector_prop,
                    **keyword_props,
                }
            },
        }

    def _build_search_query(
        self,
        query_embedding: list[float],
        top_k: int,
        filter_clauses: list[dict[str, Any]],
        query_text: str | None,
    ) -> dict[str, Any]:
        if self.es_compat:
            knn_clause: dict[str, Any] = {
                "knn": {
                    _VECTOR_FIELD: {
                        "query_vector": query_embedding,
                        "k": top_k,
                        "num_candidates": top_k * 10,
                    }
                }
            }
        else:
            knn_clause = {
                "knn": {
                    _VECTOR_FIELD: {
                        "vector": query_embedding,
                        "k": top_k,
                    }
                }
            }

        if not filter_clauses and not query_text:
            return {"query": knn_clause}

        must: list[dict[str, Any]] = [knn_clause]
        if query_text:
            must.append({"match": {_CONTENT_FIELD: {"query": query_text, "boost": 0.3}}})

        bool_query: dict[str, Any] = {"must": must}
        if filter_clauses:
            bool_query["filter"] = filter_clauses

        return {"query": {"bool": bool_query}}

    def _build_filter_clauses(
        self,
        filters: MetadataFilters | None,
        namespace: str | None,
    ) -> list[dict[str, Any]]:
        clauses: list[dict[str, Any]] = []

        if namespace:
            clauses.append({"term": {"namespace": namespace}})

        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                if key not in _KEYWORD_FIELDS:
                    logger.debug(
                        "Filter key %r is not a keyword field in OpenSearch; skipping.",
                        key,
                    )
                    continue
                clauses.append({"term": {key: value}})

        return clauses

    def _build_doc_body(
        self,
        document: dict[str, Any],
        embedding: list[float],
        namespace: str | None,
    ) -> dict[str, Any]:
        resolved_namespace = (
            document.get("namespace")
            if isinstance(document.get("namespace"), str) and document["namespace"].strip()
            else namespace
        )

        keyword_values = {
            field: str(document[field])
            for field in _KEYWORD_FIELDS
            if field in document and document[field] is not None and field != "namespace"
        }
        if resolved_namespace:
            keyword_values["namespace"] = str(resolved_namespace)

        remaining = {
            key: value
            for key, value in document.items()
            if key not in {"id", "content", "text", _VECTOR_FIELD} | _KEYWORD_FIELDS
        }

        return {
            _CONTENT_FIELD: str(document.get("content", document.get("text", ""))),
            _VECTOR_FIELD: embedding,
            _METADATA_JSON_FIELD: json.dumps(remaining, ensure_ascii=True, sort_keys=True),
            **keyword_values,
        }

    def _client(self):
        try:
            from opensearchpy import OpenSearch, RequestsHttpConnection
        except ImportError as exc:
            raise ImportError(
                "opensearch-py is required for the opensearch backend. "
                "Install with: pip install 'opensearch-py>=2.4'"
            ) from exc

        kwargs: dict[str, Any] = {
            "hosts": [self.url],
            "connection_class": RequestsHttpConnection,
            "use_ssl": self.url.startswith("https"),
            "verify_certs": self.url.startswith("https"),
        }

        if self.api_key:
            kwargs["http_auth"] = ("", self.api_key)
        elif self.username and self.password:
            kwargs["http_auth"] = (self.username, self.password)

        return OpenSearch(**kwargs)

    @staticmethod
    def _decode_metadata_json(raw: str | None) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
