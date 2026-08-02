"""
Chroma Vector Store Provider

Implements VectorStoreProvider interface for ChromaDB.
Provides local vector storage and similarity search capabilities.
"""

import json
import logging
from pathlib import Path
from typing import Any

from cerebro.interfaces.vector_store import (
    MetadataFilters,
    StoredVectorDocument,
    VectorSearchResult,
    VectorStoreProvider,
)

logger = logging.getLogger("cerebro.providers.chroma")


class ChromaVectorStoreProvider(VectorStoreProvider):
    """
    Chroma Vector Store Provider

    Implements vector storage and retrieval using ChromaDB.
    Supports local persistence and in-memory operation.
    """

    backend_name = "chroma"
    DEFAULT_COLLECTION_NAME = "cerebro_documents"
    LEGACY_COLLECTION_NAME = "phantom_documents"

    def __init__(
        self,
        persist_directory: str = "./data/vector_db",
        collection_name: str | None = None,
        default_namespace: str | None = None,
    ):
        """
        Initialize Chroma Vector Store Provider.

        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the collection to use. Defaults to the
                Cerebro collection name and automatically falls back to the
                legacy Phantom collection when opening existing persisted data.
        """
        try:
            import chromadb
        except ImportError as exc:
            raise ImportError(
                "chromadb is required for vector storage. "
                "Re-enter the project with `nix develop --command ...` so the "
                "Chroma dependencies are available."
            ) from exc

        self.persist_directory = persist_directory
        self.default_namespace = default_namespace

        # Create persist directory if it doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize Chroma client with persistence
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = self._resolve_collection_name(collection_name)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def _resolve_collection_name(self, requested_name: str | None) -> str:
        if requested_name:
            return requested_name

        try:
            existing_names = {
                getattr(collection, "name", collection)
                for collection in self.client.list_collections()
            }
        except Exception as exc:
            logger.warning("Could not list Chroma collections; defaulting to %r: %s", self.DEFAULT_COLLECTION_NAME, exc)
            existing_names = set()

        if self.DEFAULT_COLLECTION_NAME in existing_names:
            return self.DEFAULT_COLLECTION_NAME

        if self.LEGACY_COLLECTION_NAME in existing_names:
            logger.info("Using legacy Chroma collection %r.", self.LEGACY_COLLECTION_NAME)
            return self.LEGACY_COLLECTION_NAME

        return self.DEFAULT_COLLECTION_NAME

    def add_documents(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[list[float]],
        namespace: str | None = None,
        **kwargs,
    ) -> int:
        """
        Add documents with their embeddings to the vector store.

        Args:
            documents: List of document dictionaries with metadata
            embeddings: List of embedding vectors corresponding to documents
            **kwargs: Additional provider-specific parameters

        Returns:
            Number of documents successfully added
        """
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Number of documents ({len(documents)}) must match "
                f"number of embeddings ({len(embeddings)})"
            )

        if not documents:
            return 0

        # Prepare data for Chroma
        ids: list[str] = []
        metadatas: list[dict[str, Any]] = []
        documents_text: list[str] = []
        resolved_namespace = namespace or self.default_namespace

        for i, doc in enumerate(documents):
            # Use document ID if available, otherwise generate one
            doc_id = str(doc.get("id", f"doc_{i}"))
            ids.append(doc_id)

            # Extract text content
            text = str(doc.get("content", doc.get("text", "")))
            documents_text.append(text)

            # Prepare metadata (exclude content to save space)
            document_namespace = self._resolve_document_namespace(doc, resolved_namespace)
            metadata = {
                k: self._normalize_metadata_value(v)
                for k, v in doc.items()
                if k not in ["content", "text", "id"]
            }
            if document_namespace:
                metadata["namespace"] = document_namespace
            metadatas.append(metadata)

        try:
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents_text,
                metadatas=metadatas,
            )
            return len(documents)
        except Exception as e:
            logger.exception("Failed to add documents to Chroma: %s", e)
            raise

    def upsert_documents(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[list[float]],
        namespace: str | None = None,
        **kwargs,
    ) -> int:
        """Use Chroma's native upsert semantics for idempotent ingestion."""

        if len(documents) != len(embeddings):
            raise ValueError(
                f"Number of documents ({len(documents)}) must match "
                f"number of embeddings ({len(embeddings)})"
            )

        if not documents:
            return 0

        ids: list[str] = []
        metadatas: list[dict[str, Any]] = []
        documents_text: list[str] = []
        resolved_namespace = namespace or self.default_namespace

        for i, doc in enumerate(documents):
            doc_id = str(doc.get("id", f"doc_{i}"))
            ids.append(doc_id)
            documents_text.append(str(doc.get("content", doc.get("text", ""))))

            document_namespace = self._resolve_document_namespace(doc, resolved_namespace)
            metadata = {
                k: self._normalize_metadata_value(v)
                for k, v in doc.items()
                if k not in ["content", "text", "id"]
            }
            if document_namespace:
                metadata["namespace"] = document_namespace
            metadatas.append(metadata)

        try:
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents_text,
                metadatas=metadatas,
            )
            return len(documents)
        except Exception as e:
            logger.exception("Failed to upsert documents into Chroma: %s", e)
            raise

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: MetadataFilters | None = None,
        namespace: str | None = None,
        min_score: float | None = None,
        **kwargs,
    ) -> list[VectorSearchResult]:
        """
        Search for documents similar to the query embedding.

        Args:
            query_embedding: The query embedding vector
            top_k: Number of top results to return
            **kwargs: Additional provider-specific parameters

        Returns:
            List of documents with similarity scores, sorted by relevance
        """
        try:
            where = self._build_where_clause(filters, namespace)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            # Transform Chroma results to standard format
            documents: list[VectorSearchResult] = []

            if results and results["ids"] and len(results["ids"]) > 0:
                for i, doc_id in enumerate(results["ids"][0]):
                    # Chroma returns distances, convert to similarity (1 - distance for cosine)
                    distance = results["distances"][0][i] if results["distances"] else 0
                    similarity = 1 - distance  # For cosine distance
                    if min_score is not None and similarity < min_score:
                        continue

                    metadata = (
                        results["metadatas"][0][i]
                        if results["metadatas"]
                        else {}
                    ) or {}

                    doc = VectorSearchResult(
                        id=str(doc_id),
                        content=results["documents"][0][i] if results["documents"] else "",
                        metadata=metadata,
                        score=float(similarity),
                        distance=float(distance),
                        namespace=metadata.get("namespace"),
                        title=metadata.get("title"),
                        source=metadata.get("source"),
                    )
                    documents.append(doc)

            return documents
        except Exception as e:
            logger.exception("Failed to search Chroma: %s", e)
            raise

    def delete_documents(
        self,
        document_ids: list[str],
        namespace: str | None = None,
    ) -> int:
        """
        Delete documents from the vector store.

        Args:
            document_ids: List of document IDs to delete

        Returns:
            Number of documents successfully deleted
        """
        if not document_ids:
            return 0

        try:
            self.collection.delete(ids=document_ids)
            return len(document_ids)
        except Exception as e:
            logger.exception("Failed to delete documents from Chroma: %s", e)
            raise

    def clear(self, namespace: str | None = None) -> None:
        """
        Clear all documents from the vector store.
        """
        try:
            where = self._build_where_clause(None, namespace)
            all_docs = self.collection.get(where=where)
            if all_docs and all_docs["ids"]:
                self.collection.delete(ids=all_docs["ids"])
        except Exception as e:
            logger.exception("Failed to clear Chroma collection: %s", e)
            raise

    def get_document_count(self, namespace: str | None = None) -> int:
        """
        Get the total number of documents in the vector store.

        Returns:
            Number of documents
        """
        try:
            where = self._build_where_clause(None, namespace)
            if where:
                results = self.collection.get(where=where)
                return len(results.get("ids", [])) if results else 0
            return self.collection.count()
        except Exception as e:
            logger.exception("Failed to get document count from Chroma: %s", e)
            raise

    def export_documents(
        self,
        namespace: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[StoredVectorDocument]:
        """Export documents and embeddings from Chroma for backend migration."""

        try:
            where = self._build_where_clause(None, namespace)
            results = self.collection.get(
                where=where,
                limit=limit,
                offset=offset,
                include=["documents", "metadatas", "embeddings"],
            )
        except Exception as e:
            logger.exception("Failed to export documents from Chroma: %s", e)
            raise

        ids = results.get("ids", []) if results else []
        metadatas = results.get("metadatas", []) if results else []
        documents = results.get("documents", []) if results else []
        embeddings = results.get("embeddings", []) if results else []

        exported: list[StoredVectorDocument] = []
        for index, doc_id in enumerate(ids):
            metadata = (metadatas[index] if index < len(metadatas) else {}) or {}
            content = documents[index] if index < len(documents) else ""
            embedding = embeddings[index] if index < len(embeddings) else []
            exported.append(
                StoredVectorDocument(
                    id=str(doc_id),
                    content=str(content or ""),
                    metadata=dict(metadata),
                    embedding=[float(value) for value in embedding],
                    namespace=metadata.get("namespace"),
                    title=metadata.get("title"),
                    source=metadata.get("source"),
                )
            )

        return exported

    def health_check(self) -> bool:
        """
        Check if the vector store is healthy and accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to get collection count as a health check
            self.collection.count()
            return True
        except Exception as e:
            logger.warning("Chroma health check failed: %s", e)
            return False

    def get_collection_info(self) -> dict[str, Any]:
        """
        Get information about the current collection.

        Returns:
            Dictionary with collection metadata
        """
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
            }
        except Exception as e:
            logger.warning("Failed to get Chroma collection info: %s", e)
            return {}

    def get_backend_info(self) -> dict[str, Any]:
        """Return backend metadata for diagnostics and health endpoints."""

        return {
            "backend": self.backend_name,
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "default_namespace": self.default_namespace,
            "supports_filters": True,
            "supports_namespace": True,
            "production_ready": False,
            "development_only": True,
        }

    @staticmethod
    def _normalize_metadata_value(value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return json.dumps(value, ensure_ascii=True)

    def _build_where_clause(
        self,
        filters: MetadataFilters | None,
        namespace: str | None,
    ) -> dict[str, Any] | None:
        where: dict[str, Any] = {}
        resolved_namespace = namespace or self.default_namespace
        if resolved_namespace:
            where["namespace"] = resolved_namespace
        if filters:
            where.update({k: v for k, v in filters.items() if v is not None})
        return where or None

    @staticmethod
    def _resolve_document_namespace(
        document: dict[str, Any],
        fallback_namespace: str | None,
    ) -> str | None:
        explicit_namespace = document.get("namespace")
        if isinstance(explicit_namespace, str) and explicit_namespace.strip():
            return explicit_namespace
        return fallback_namespace
