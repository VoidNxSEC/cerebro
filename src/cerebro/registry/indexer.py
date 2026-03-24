"""
Knowledge Indexer

Indexes intelligence items into a vector store for semantic search.
Uses FAISS for efficient similarity search and sentence-transformers for embeddings.
"""

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger("cerebro.indexer")

# Lazy imports for heavy dependencies
_faiss = None
_sentence_transformer = None


def get_faiss():
    """Lazy load FAISS."""
    global _faiss
    if _faiss is None:
        try:
            import faiss
            _faiss = faiss
        except ImportError:
            logger.warning("FAISS not available. Vector search disabled.")
            return None
    return _faiss


def get_sentence_transformer():
    """Lazy load sentence-transformers."""
    global _sentence_transformer
    if _sentence_transformer is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_transformer = SentenceTransformer
        except ImportError:
            logger.warning("sentence-transformers not available. Embeddings disabled.")
            return None
    return _sentence_transformer


class KnowledgeIndexer:
    """
    Indexes knowledge into a vector store for semantic search.

    Features:
    - Semantic similarity search
    - Hybrid search (keyword + semantic)
    - Incremental indexing
    - Persistent storage
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"  # Fast, good quality
    EMBEDDING_DIM = 384  # Dimension for MiniLM

    def __init__(
        self,
        cerebro: "CerebroIntelligence",
        model_name: str = DEFAULT_MODEL,
        cache_dir: str = "./data/embeddings",
    ):
        self.cerebro = cerebro
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize embedder lazily
        self._embedder = None

        # FAISS index
        self._index = None
        self._id_map: List[str] = []  # Maps FAISS index to item IDs

        # Load existing index if available
        self._load_index()

    @property
    def embedder(self):
        """Lazy load the sentence transformer model."""
        if self._embedder is None:
            SentenceTransformer = get_sentence_transformer()
            if SentenceTransformer:
                logger.info(f"Loading embedding model: {self.model_name}")
                self._embedder = SentenceTransformer(self.model_name)
        return self._embedder

    @property
    def index(self):
        """Get or create FAISS index."""
        if self._index is None:
            faiss = get_faiss()
            if faiss:
                # Create a flat inner product index (cosine similarity)
                self._index = faiss.IndexFlatIP(self.EMBEDDING_DIM)
        return self._index

    def _get_index_path(self) -> Path:
        """Get path to index file."""
        return self.cache_dir / "faiss_index.bin"

    def _get_id_map_path(self) -> Path:
        """Get path to ID map file."""
        return self.cache_dir / "id_map.json"

    def _load_index(self) -> bool:
        """Load index from disk."""
        index_path = self._get_index_path()
        id_map_path = self._get_id_map_path()

        if not index_path.exists() or not id_map_path.exists():
            return False

        try:
            faiss = get_faiss()
            if faiss is None:
                return False

            self._index = faiss.read_index(str(index_path))
            with open(id_map_path, "r") as f:
                self._id_map = json.load(f)

            logger.info(f"Loaded index with {len(self._id_map)} items")
            return True
        except Exception as e:
            logger.warning(f"Failed to load index: {e}")
            return False

    def _save_index(self) -> bool:
        """Save index to disk."""
        if self._index is None:
            return False

        try:
            faiss = get_faiss()
            if faiss is None:
                return False

            faiss.write_index(self._index, str(self._get_index_path()))
            with open(self._get_id_map_path(), "w") as f:
                json.dump(self._id_map, f)

            logger.info(f"Saved index with {len(self._id_map)} items")
            return True
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            return False

    def embed_text(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text."""
        if self.embedder is None:
            return None

        try:
            embedding = self.embedder.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return None

    def embed_texts(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings for multiple texts."""
        if self.embedder is None:
            return None

        try:
            embeddings = self.embedder.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return None

    def index_item(self, item_id: str, content: str) -> bool:
        """Index a single intelligence item."""
        if self.index is None or self.embedder is None:
            return False

        # Check if already indexed
        if item_id in self._id_map:
            return True

        try:
            import numpy as np

            embedding = self.embed_text(content)
            if embedding is None:
                return False

            # Add to FAISS
            embedding_array = np.array([embedding], dtype="float32")
            self.index.add(embedding_array)
            self._id_map.append(item_id)

            return True
        except Exception as e:
            logger.error(f"Failed to index item {item_id}: {e}")
            return False

    def index_all(self, batch_size: int = 100) -> int:
        """
        Index all intelligence items in Cerebro.

        Args:
            batch_size: Number of items to process at once

        Returns:
            Number of items indexed
        """
        if self.embedder is None:
            logger.warning("Embedder not available, skipping indexing")
            return 0

        items = list(self.cerebro._intelligence.values())
        indexed = 0

        # Process in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            # Filter out already indexed items
            new_items = [
                item for item in batch
                if item.id not in self._id_map
            ]

            if not new_items:
                continue

            # Generate embeddings
            texts = [
                f"{item.title}. {item.content[:500]}"
                for item in new_items
            ]

            embeddings = self.embed_texts(texts)
            if embeddings is None:
                continue

            # Add to index
            try:
                import numpy as np

                embedding_array = np.array(embeddings, dtype="float32")
                self.index.add(embedding_array)

                for item in new_items:
                    self._id_map.append(item.id)
                    indexed += 1

            except Exception as e:
                logger.error(f"Failed to add batch to index: {e}")

        # Save index
        self._save_index()

        logger.info(f"Indexed {indexed} new items. Total: {len(self._id_map)}")
        return indexed

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.3,
    ) -> List[Tuple[str, float]]:
        """
        Search for similar items.

        Args:
            query: Search query
            top_k: Number of results to return
            min_score: Minimum similarity score (0-1)

        Returns:
            List of (item_id, score) tuples
        """
        if self.index is None or self.embedder is None or len(self._id_map) == 0:
            return []

        try:
            import numpy as np

            # Generate query embedding
            query_embedding = self.embed_text(query)
            if query_embedding is None:
                return []

            query_array = np.array([query_embedding], dtype="float32")

            # Search
            scores, indices = self.index.search(query_array, min(top_k, len(self._id_map)))

            # Map indices to item IDs
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and score >= min_score:
                    item_id = self._id_map[idx]
                    results.append((item_id, float(score)))

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def semantic_query(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search with full item details.

        Args:
            query: Search query
            top_k: Number of results
            min_score: Minimum score threshold

        Returns:
            List of intelligence items with scores
        """
        results = self.search(query, top_k, min_score)

        items = []
        for item_id, score in results:
            item = self.cerebro.get_intelligence(item_id)
            if item:
                items.append({
                    "id": item.id,
                    "type": item.type.value,
                    "title": item.title,
                    "content": item.content[:500],
                    "source": item.source,
                    "score": round(score, 3),
                    "tags": item.tags,
                    "related_projects": item.related_projects,
                })

        return items

    def get_stats(self) -> Dict[str, Any]:
        """Get indexer statistics."""
        return {
            "model": self.model_name,
            "embedding_dim": self.EMBEDDING_DIM,
            "indexed_items": len(self._id_map),
            "index_size_mb": self._get_index_path().stat().st_size / 1024 / 1024
            if self._get_index_path().exists() else 0,
        }

    def clear(self) -> None:
        """Clear the index."""
        faiss = get_faiss()
        if faiss:
            self._index = faiss.IndexFlatIP(self.EMBEDDING_DIM)
        self._id_map = []
        self._save_index()
        logger.info("Index cleared")
