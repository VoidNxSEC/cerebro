"""
cerebro.core.rag.embeddings
────────────────────────────
Embedding system with automatic model selection by content type.

Why jina-embeddings-v2-base-code?
  - 8192 token context (vs 512 for all-MiniLM)
  - Trained specifically on source code
  - Understands syntactic structure, not just text tokens
  - Supports code-to-code and text-to-code search

For code intelligence RAG this is the difference between
real semantic retrieval and glorified keyword matching.

Usage:
    system = EmbeddingSystem(strategy="code")
    vectors = system.embed(["def foo(): ...", "class Bar: ..."])
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("cerebro.embeddings")


class EmbeddingModel(Enum):
    """
    Available models by use case.
    Preference order: code > prose > fallback.
    """
    # Code-aware — best for code RAG
    JINA_CODE    = "jinaai/jina-embeddings-v2-base-code"    # 8192 ctx, recommended

    # Prose — docs, READMEs, long comments
    MPNET        = "sentence-transformers/all-mpnet-base-v2"  # 768 dim, good quality

    # Lightweight fallback — available in nix shell
    MINILM       = "sentence-transformers/all-MiniLM-L6-v2"   # 384 dim, fast

    # Reranker (cross-encoder, not bi-encoder) — cached in data/models/
    RERANKER     = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@dataclass
class EmbeddingResult:
    vectors: list[list[float]]
    model_used: str
    dimension: int
    latency_ms: float
    batch_size: int


class EmbeddingSystem:
    """
    Embedding system with:
      - Automatic model selection by content type
      - Batching to respect memory limits
      - In-process model cache (avoids reload on each call)
      - Graceful fallback: jina → mpnet → minilm
    """

    # Loaded model cache — singleton per process
    _model_cache: dict[str, object] = {}

    def __init__(
        self,
        strategy: str = "auto",       # "code", "prose", "auto"
        batch_size: int = 32,
        prefer_local: bool = True,     # True = carrega modelo local; False = tenta API
        device: str = "auto",          # "cpu", "cuda", "auto"
    ):
        self.strategy    = strategy
        self.batch_size  = batch_size
        self.prefer_local = prefer_local
        self.device      = self._resolve_device(device)

    def embed(self, texts: list[str], content_type: str = "code") -> EmbeddingResult:
        """
        Generate embeddings for a list of texts.

        Args:
            texts:        list of strings to embed
            content_type: "code" or "prose" for model selection
        """
        if not texts:
            return EmbeddingResult([], "", 0, 0.0, 0)

        model_name = self._select_model(content_type)
        model      = self._load_model(model_name)

        t0 = time.time()
        vectors = self._batch_embed(model, texts, model_name)
        latency = (time.time() - t0) * 1000

        dim = len(vectors[0]) if vectors else 0

        logger.info(
            "embeddings_generated",
            extra={
                "model":      model_name.split("/")[-1],
                "n_texts":    len(texts),
                "dimension":  dim,
                "latency_ms": round(latency, 2),
                "device":     self.device,
            }
        )

        return EmbeddingResult(
            vectors=vectors,
            model_used=model_name,
            dimension=dim,
            latency_ms=latency,
            batch_size=self.batch_size,
        )

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query — convenience method."""
        result = self.embed([query], content_type="prose")
        return result.vectors[0] if result.vectors else []

    def _select_model(self, content_type: str) -> str:
        """
        Select model based on content type and availability.
        Hierarchical fallback: jina → mpnet → minilm.
        """
        if self.strategy == "code" or content_type == "code":
            candidates = [
                EmbeddingModel.JINA_CODE.value,
                EmbeddingModel.MPNET.value,
                EmbeddingModel.MINILM.value,
            ]
        else:
            candidates = [
                EmbeddingModel.MPNET.value,
                EmbeddingModel.MINILM.value,
            ]

        for model_name in candidates:
            if self._is_model_available(model_name):
                return model_name

        # Last resort fallback — always available with sentence-transformers
        return EmbeddingModel.MINILM.value

    def _is_model_available(self, model_name: str) -> bool:
        """Check if the model is in local cache or can be downloaded."""
        if model_name in self._model_cache:
            return True

        try:
            import sentence_transformers  # noqa
            return True
        except ImportError:
            return False

    def _load_model(self, model_name: str):
        """Load model with in-memory cache."""
        if model_name in self._model_cache:
            return self._model_cache[model_name]

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {model_name}")
            model = SentenceTransformer(model_name, device=self.device)
            self._model_cache[model_name] = model
            logger.info(f"Model loaded: {model_name} on {self.device}")
            return model
        except Exception as e:
            logger.error(f"Failed to load {model_name}: {e}")
            fallback = EmbeddingModel.MINILM.value
            if fallback not in self._model_cache:
                from sentence_transformers import SentenceTransformer
                self._model_cache[fallback] = SentenceTransformer(fallback, device=self.device)
            return self._model_cache[fallback]

    def _batch_embed(self, model, texts: list[str], model_name: str) -> list[list[float]]:
        """
        Batch processing to avoid memory exhaustion with large corpora.
        """
        all_vectors = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]

            try:
                vectors = model.encode(
                    batch,
                    normalize_embeddings=True,  # cosine similarity funciona melhor
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                all_vectors.extend(vectors.tolist())

            except Exception as e:
                logger.warning(
                    f"Batch {i//self.batch_size} failed: {e}. "
                    f"Using zero vectors as fallback."
                )
                # Zero vectors as fallback — degraded but does not crash
                dim = 768  # default mpnet dim
                all_vectors.extend([[0.0] * dim] * len(batch))

        return all_vectors

    def _resolve_device(self, device: str) -> str:
        if device != "auto":
            return device
        try:
            import torch
            if torch.cuda.is_available():
                logger.info("CUDA available — using GPU for embeddings")
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    @classmethod
    def clear_cache(cls):
        """Release models from memory — useful in tests."""
        cls._model_cache.clear()
        logger.info("Embedding model cache cleared")


# ─── Convenience functions ───────────────────────────────────────────────────

_default_system: EmbeddingSystem | None = None

def get_embedding_system(**kwargs) -> EmbeddingSystem:
    """Global singleton — reuses loaded models across calls."""
    global _default_system
    if _default_system is None:
        _default_system = EmbeddingSystem(**kwargs)
    return _default_system
