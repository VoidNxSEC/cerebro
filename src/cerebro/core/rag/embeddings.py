"""
cerebro.core.rag.embeddings
────────────────────────────
Embedding system com seleção automática por tipo de conteúdo.

Por que jina-embeddings-v2-base-code?
  - 8192 token context (vs 512 do all-MiniLM)
  - Treinado especificamente em código fonte
  - Entende estrutura sintática, não só tokens de texto
  - Suporta code-to-code e text-to-code search

Para um RAG de code intelligence é a diferença entre
retrieval semântico real e keyword matching glorificado.

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
    Modelos disponíveis por caso de uso.
    Ordem de preferência: code > prose > fallback.
    """
    # Code-aware — melhor para RAG de código
    JINA_CODE    = "jinaai/jina-embeddings-v2-base-code"    # 8192 ctx, recomendado

    # Prosa — docs, README, comentários longos
    MPNET        = "sentence-transformers/all-mpnet-base-v2"  # 768 dim, boa qualidade

    # Fallback leve — já disponível no nix shell
    MINILM       = "sentence-transformers/all-MiniLM-L6-v2"   # 384 dim, rápido

    # Reranker (cross-encoder, não bi-encoder) — já cacheado em data/models/
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
    Sistema de embedding com:
      - Seleção automática de modelo por content type
      - Batching para respeitar limites de memória/API
      - Cache de modelo em memória (evita reload a cada call)
      - Fallback gracioso: jina → mpnet → minilm
    """

    # Cache de modelos carregados — singleton por processo
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
        Gera embeddings para uma lista de textos.

        Args:
            texts:        lista de strings para embedar
            content_type: "code" ou "prose" para seleção de modelo
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
        """Embed de query única — convenience method."""
        result = self.embed([query], content_type="prose")
        return result.vectors[0] if result.vectors else []

    def _select_model(self, content_type: str) -> str:
        """
        Seleciona modelo baseado no content type e disponibilidade.
        Fallback hierárquico: jina → mpnet → minilm.
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

        # Último fallback — sempre disponível com sentence-transformers
        return EmbeddingModel.MINILM.value

    def _is_model_available(self, model_name: str) -> bool:
        """Verifica se o modelo está no cache local ou é baixável."""
        # Se já carregado — disponível
        if model_name in self._model_cache:
            return True

        # Tenta importar sentence_transformers
        try:
            import sentence_transformers  # noqa
            return True  # pode tentar baixar
        except ImportError:
            return False

    def _load_model(self, model_name: str):
        """Carrega modelo com cache em memória."""
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
            # Fallback para MiniLM
            fallback = EmbeddingModel.MINILM.value
            if fallback not in self._model_cache:
                from sentence_transformers import SentenceTransformer
                self._model_cache[fallback] = SentenceTransformer(fallback, device=self.device)
            return self._model_cache[fallback]

    def _batch_embed(self, model, texts: list[str], model_name: str) -> list[list[float]]:
        """
        Batching para não explodir memória com corpora grandes.
        Vertex AI tem limite de 250 docs/batch — respeitado aqui.
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
                    f"Usando zero vectors como fallback."
                )
                # Zero vectors como fallback — degraded mas não quebra
                dim = 768  # default mpnet dim
                all_vectors.extend([[0.0] * dim] * len(batch))

        return all_vectors

    def _resolve_device(self, device: str) -> str:
        if device != "auto":
            return device
        try:
            import torch
            if torch.cuda.is_available():
                logger.info("CUDA disponível — usando GPU para embeddings")
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    @classmethod
    def clear_cache(cls):
        """Libera modelos da memória — útil em testes."""
        cls._model_cache.clear()
        logger.info("Embedding model cache cleared")


# ─── Convenience functions ───────────────────────────────────────────────────

_default_system: EmbeddingSystem | None = None

def get_embedding_system(**kwargs) -> EmbeddingSystem:
    """Singleton global — reutiliza modelos carregados entre calls."""
    global _default_system
    if _default_system is None:
        _default_system = EmbeddingSystem(**kwargs)
    return _default_system
