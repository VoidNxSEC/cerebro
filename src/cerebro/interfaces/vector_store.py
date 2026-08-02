"""
VectorStoreProvider Interface

Defines the abstract base class for Vector Store providers.
Implementations should handle:
- Storing and retrieving vectors
- Similarity search
- Document management
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar

type MetadataScalar = str | int | float | bool | None
type MetadataFilters = dict[str, MetadataScalar]


@dataclass(frozen=True, slots=True)
class VectorSearchResult:
    """Normalized retrieval result returned by vector store providers."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    distance: float | None = None
    namespace: str | None = None
    title: str | None = None
    source: str | None = None


@dataclass(frozen=True, slots=True)
class VectorStoreHealth:
    """Structured health status for vector store providers."""

    healthy: bool
    backend: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StoredVectorDocument:
    """Normalized exported document payload for backend-to-backend migrations."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] = field(default_factory=list)
    namespace: str | None = None
    title: str | None = None
    source: str | None = None

    def to_document(self) -> dict[str, Any]:
        """Convert the exported payload back into an ingestible document dict."""

        document = {
            "id": self.id,
            "content": self.content,
            **self.metadata,
        }
        if self.namespace is not None:
            document["namespace"] = self.namespace
        if self.title is not None:
            document["title"] = self.title
        if self.source is not None:
            document["source"] = self.source
        return document


class VectorStoreProvider(ABC):
    """
    Abstract base class for Vector Store providers.

    Implementations must provide methods for:
    - Adding documents with embeddings
    - Searching for similar documents
    - Deleting documents
    - Health checks
    """

    backend_name: ClassVar[str] = "unknown"

    def initialize_schema(self, **kwargs) -> dict[str, Any]:
        """
        Initialize backend-specific storage structures.

        Providers that need explicit bootstrap steps, such as PostgreSQL-backed
        vector stores, should override this hook. Local embedded providers can
        keep the default no-op implementation.
        """

        return self.get_backend_info()

    def upsert_documents(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[list[float]],
        namespace: str | None = None,
        **kwargs,
    ) -> int:
        """
        Upsert documents into the vector store.

        Providers may override this to use native upsert semantics.
        The default implementation falls back to `add_documents`.
        """

        return self.add_documents(
            documents,
            embeddings,
            namespace=namespace,
            **kwargs,
        )

    @abstractmethod
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
            namespace: Logical namespace/tenant for the write
            **kwargs: Additional provider-specific parameters

        Returns:
            Number of documents successfully added
        """

    @abstractmethod
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
            filters: Metadata filters to apply
            namespace: Logical namespace/tenant for the query
            min_score: Optional minimum normalized score threshold
            **kwargs: Additional provider-specific parameters

        Returns:
            List of documents with similarity scores, sorted by relevance
        """

    @abstractmethod
    def delete_documents(
        self,
        document_ids: list[str],
        namespace: str | None = None,
    ) -> int:
        """
        Delete documents from the vector store.

        Args:
            document_ids: List of document IDs to delete
            namespace: Optional namespace scope

        Returns:
            Number of documents successfully deleted
        """

    @abstractmethod
    def clear(self, namespace: str | None = None) -> None:
        """
        Clear all documents from the vector store.
        """

    @abstractmethod
    def get_document_count(self, namespace: str | None = None) -> int:
        """
        Get the total number of documents in the vector store.

        Returns:
            Number of documents
        """

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the vector store is healthy and accessible.

        Returns:
            True if healthy, False otherwise
        """

    def get_backend_info(self) -> dict[str, Any]:
        """Return structured backend metadata for observability and health output."""

        return {"backend": self.backend_name}

    def export_documents(
        self,
        namespace: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[StoredVectorDocument]:
        """
        Export documents with embeddings for backend-to-backend migration.

        Providers should override this when they can efficiently enumerate
        stored rows. The default implementation makes the limitation explicit.
        """

        raise NotImplementedError(
            f"Vector store backend {self.backend_name!r} does not implement export_documents()."
        )

    def health_status(self) -> VectorStoreHealth:
        """Return a structured health status while keeping `health_check()` for compatibility."""

        return VectorStoreHealth(
            healthy=self.health_check(),
            backend=self.backend_name,
            details=self.get_backend_info(),
        )
