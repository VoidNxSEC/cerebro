"""
Knowledge Indexer

Indexes intelligence items into the configured vector store for semantic
search, using the shared provider layer introduced for production RAG.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cerebro.core.rag.embeddings import EmbeddingSystem
from cerebro.intelligence.core import IntelligenceItem, IntelligenceType
from cerebro.interfaces.vector_store import VectorStoreProvider
from cerebro.providers.vector_store_factory import build_vector_store_provider
from cerebro.settings import get_settings

if TYPE_CHECKING:
    from cerebro.intelligence.core import CerebroIntelligence

logger = logging.getLogger("cerebro.indexer")


class KnowledgeIndexer:
    """
    Indexes knowledge into the configured vector store for semantic search.

    The old FAISS-only path has been replaced by the provider layer so API chat,
    semantic search, and production RAG can converge on the same backend.
    """

    DEFAULT_MODEL = "code-aware-auto"

    def __init__(
        self,
        cerebro: CerebroIntelligence,
        model_name: str = DEFAULT_MODEL,
        cache_dir: str = "./data/embeddings",
        vector_store_provider: VectorStoreProvider | None = None,
        vector_store_namespace: str | None = None,
    ):
        self.cerebro = cerebro
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        settings = get_settings()
        if vector_store_namespace is not None:
            self.vector_store_namespace = vector_store_namespace
        elif vector_store_provider is not None:
            self.vector_store_namespace = getattr(
                vector_store_provider,
                "default_namespace",
                None,
            )
        else:
            self.vector_store_namespace = settings.vector_store_namespace
        self.vector_store_provider = vector_store_provider or build_vector_store_provider(
            collection_name=settings.vector_store_collection_name,
            namespace=self.vector_store_namespace,
        )
        self._embedding_system = EmbeddingSystem(strategy="code")

    @property
    def embedder(self) -> EmbeddingSystem:
        """Compatibility shim for older call sites."""

        return self._embedding_system

    def embed_text(self, text: str) -> list[float] | None:
        """Generate an embedding for a single text payload."""

        if not text:
            return None

        try:
            return self._embedding_system.embed([text], content_type="code").vectors[0]
        except Exception as exc:
            logger.error("Embedding failed: %s", exc)
            return None

    def embed_texts(self, texts: list[str]) -> list[list[float]] | None:
        """Generate embeddings for multiple texts."""

        if not texts:
            return []

        try:
            return self._embedding_system.embed(texts, content_type="code").vectors
        except Exception as exc:
            logger.error("Batch embedding failed: %s", exc)
            return None

    def index_item(self, item_id: str, content: str) -> bool:
        """Index a single intelligence item."""

        try:
            embedding = self.embed_text(content)
            if embedding is None:
                return False

            item = self.cerebro.get_intelligence(item_id)
            document = (
                self._item_to_document(item)
                if item is not None
                else {"id": item_id, "title": item_id, "content": content, "source": "unknown"}
            )

            self.vector_store_provider.initialize_schema()
            self.vector_store_provider.upsert_documents(
                [document],
                [embedding],
                namespace=self.vector_store_namespace,
            )
            return True
        except Exception as exc:
            logger.error("Failed to index item %s: %s", item_id, exc)
            return False

    def index_all(self, batch_size: int = 100) -> int:
        """
        Index all intelligence items in Cerebro.

        Returns the net number of newly indexed items when the backend can
        report counts; otherwise it falls back to the number of processed rows.
        """

        items = list(self.cerebro._intelligence.values())
        if not items:
            return 0

        try:
            self.vector_store_provider.initialize_schema()
        except Exception as exc:
            logger.error("Vector store bootstrap failed: %s", exc)
            return 0

        before_count = self._safe_document_count()
        processed = 0

        for offset in range(0, len(items), batch_size):
            batch = items[offset:offset + batch_size]
            texts = [self._item_to_index_text(item) for item in batch]
            embeddings = self.embed_texts(texts)
            if embeddings is None:
                continue

            documents = [self._item_to_document(item) for item in batch]
            try:
                processed += self.vector_store_provider.upsert_documents(
                    documents,
                    embeddings,
                    namespace=self.vector_store_namespace,
                )
            except Exception as exc:
                logger.error("Failed to upsert intelligence batch: %s", exc)

        after_count = self._safe_document_count()
        if before_count is not None and after_count is not None:
            newly_indexed = max(after_count - before_count, 0)
        else:
            newly_indexed = processed

        logger.info(
            "Indexed %s items via %s (processed=%s, total=%s)",
            newly_indexed,
            self.vector_store_provider.backend_name,
            processed,
            after_count if after_count is not None else "unknown",
        )
        return newly_indexed

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.3,
    ) -> list[tuple[str, float]]:
        """Return (id, score) pairs for the closest documents to query."""

        if top_k <= 0:
            return []

        document_count = self._safe_document_count()
        if document_count is not None and document_count <= 0:
            return []

        try:
            query_embedding = self._embedding_system.embed_query(query)
            matches = self.vector_store_provider.search(
                query_embedding,
                top_k=top_k,
                namespace=self.vector_store_namespace,
                min_score=min_score,
            )
            return [(match.id, float(match.score)) for match in matches]
        except Exception as exc:
            logger.error("Search failed: %s", exc)
            return []

    def semantic_query(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.3,
        types: list[IntelligenceType] | None = None,
        projects: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search with full item details and optional scope filters.

        Single-type filters are pushed down to the vector store as metadata
        filters when possible, avoiding Python-side over-fetching. Multi-type
        and project filters still apply a post-retrieval pass because most
        backends cannot express OR conditions or list-membership checks cheaply.
        """

        if not query:
            return []

        document_count = self._safe_document_count()
        if document_count is not None and document_count <= 0:
            return []

        # Push a single type filter down to the vector store so the backend
        # can prune before returning results. Multiple types require OR logic
        # that not all backends support, so fall back to post-filtering there.
        store_filters = None
        post_filter_types = types
        if types and len(types) == 1:
            store_filters = {"type": types[0].value}
            post_filter_types = None

        search_window = self._resolve_search_window(top_k, post_filter_types, projects)

        try:
            query_embedding = self._embedding_system.embed_query(query)
            matches = self.vector_store_provider.search(
                query_embedding,
                top_k=search_window,
                filters=store_filters,
                namespace=self.vector_store_namespace,
                min_score=min_score,
            )
        except Exception as exc:
            logger.error("Semantic query failed: %s", exc)
            return []

        items: list[dict[str, Any]] = []
        for match in matches:
            item = self.cerebro.get_intelligence(match.id)
            if item is None:
                continue
            if post_filter_types and item.type not in post_filter_types:
                continue
            if projects and not any(p in item.related_projects for p in projects):
                continue

            items.append(
                {
                    "id": item.id,
                    "type": item.type.value,
                    "title": item.title,
                    "content": item.content[:500],
                    "source": item.source,
                    "score": round(float(match.score), 3),
                    "tags": item.tags,
                    "related_projects": item.related_projects,
                }
            )
            if len(items) >= top_k:
                break

        return items

    def get_stats(self) -> dict[str, Any]:
        """Get indexer statistics."""

        backend_info = self.vector_store_provider.get_backend_info()
        return {
            "model": self.model_name,
            "embedding_strategy": "code",
            "backend": self.vector_store_provider.backend_name,
            "namespace": self.vector_store_namespace,
            "indexed_items": self._safe_document_count(fallback=0),
            "index_size_mb": self._resolve_index_size_mb(backend_info),
            **backend_info,
        }

    def clear(self) -> None:
        """Clear the current vector namespace."""

        self.vector_store_provider.clear(namespace=self.vector_store_namespace)
        logger.info("Index cleared for namespace=%s", self.vector_store_namespace)

    def _item_to_index_text(self, item: IntelligenceItem) -> str:
        return f"{item.title}. {item.content[:500]}"

    def _item_to_document(self, item: IntelligenceItem) -> dict[str, Any]:
        return {
            "id": item.id,
            "type": item.type.value,
            "source": item.source,
            "title": item.title,
            "content": item.content,
            "tags": item.tags,
            "related_projects": item.related_projects,
            "threat_level": item.threat_level.value,
            "timestamp": item.timestamp.isoformat(),
            **{
                key: value
                for key, value in item.metadata.items()
                if isinstance(value, (str, int, float, bool)) or value is None
            },
        }

    def _resolve_search_window(
        self,
        top_k: int,
        types: list[IntelligenceType] | None,
        projects: list[str] | None,
    ) -> int:
        if not types and not projects:
            return top_k

        available = self._safe_document_count(fallback=top_k * 5)
        if available is None:
            return max(top_k * 5, top_k)
        return min(max(top_k * 5, top_k), max(available, top_k))

    def _safe_document_count(self, fallback: int | None = None) -> int | None:
        try:
            return self.vector_store_provider.get_document_count(
                namespace=self.vector_store_namespace,
            )
        except Exception as exc:
            logger.warning("Failed to get index document count: %s", exc)
            return fallback

    @staticmethod
    def _resolve_index_size_mb(backend_info: dict[str, Any]) -> float:
        persist_directory = backend_info.get("persist_directory")
        if not isinstance(persist_directory, str):
            return 0.0

        path = Path(persist_directory)
        if not path.exists():
            return 0.0

        if path.is_file():
            return path.stat().st_size / 1024 / 1024

        return sum(child.stat().st_size for child in path.rglob("*") if child.is_file()) / 1024 / 1024
