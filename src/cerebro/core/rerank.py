"""
Cross‑Encoder Reranker for post‑RAG result reordering.

Uses sentence‑transformers' CrossEncoder models to score query‑document relevance
and reorder retrieved documents before answer generation.
"""

import logging
from typing import List, Tuple, Optional, Any

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Lightweight cross‑encoder reranker for RAG results."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        max_length: int = 512,
        device: Optional[str] = None,
    ):
        """
        Initialize a cross‑encoder reranker.

        Args:
            model_name: Hugging Face model identifier (default: Microsoft's MiniLM‑L‑6‑v2)
            max_length: Maximum token length for input sequences
            device: 'cuda' or 'cpu' (auto‑detected if None)
        """
        self.model_name = model_name
        self.max_length = max_length

        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            raise ImportError(
                "sentence‑transformers is required for CrossEncoderReranker. "
                "Install with: poetry add sentence‑transformers"
            )

        self.model = CrossEncoder(model_name, max_length=max_length, device=device)
        logger.info("Loaded cross‑encoder model: %s", model_name)

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
        batch_size: int = 32,
    ) -> List[Tuple[int, float, str]]:
        """
        Rerank documents according to relevance to the query.

        Args:
            query: Search query
            documents: List of document texts to rerank
            top_k: Return only the top‑k results (None returns all)
            batch_size: Batch size for scoring

        Returns:
            List of tuples (original_index, score, document_text) sorted descending by score.
        """
        if not documents:
            return []

        # Create query‑document pairs
        pairs = [(query, doc) for doc in documents]

        # Predict scores
        scores = self.model.predict(
            pairs,
            batch_size=batch_size,
            show_progress_bar=False,
        )

        # Combine with indices
        indexed = list(enumerate(scores))
        # Sort by score descending
        indexed.sort(key=lambda x: x[1], reverse=True)

        # Apply top‑k
        if top_k is not None:
            indexed = indexed[:top_k]

        # Return (original_index, score, document)
        return [(idx, score, documents[idx]) for idx, score in indexed]

    def rerank_and_sort(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
    ) -> List[str]:
        """
        Convenience method that returns only the reranked document texts.
        """
        ranked = self.rerank(query, documents, top_k=top_k)
        return [doc for _, _, doc in ranked]


# Global default instance for easy reuse
_default_reranker: Optional[CrossEncoderReranker] = None


def get_reranker(
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    max_length: int = 512,
    device: Optional[str] = None,
) -> CrossEncoderReranker:
    """
    Singleton factory for a cross‑encoder reranker.
    """
    global _default_reranker
    if _default_reranker is None:
        _default_reranker = CrossEncoderReranker(
            model_name=model_name,
            max_length=max_length,
            device=device,
        )
    return _default_reranker


# Global client instance
_default_client: Optional[Any] = None


def get_reranker_client(
    service_url: Optional[str] = None,
    timeout: float = 1.0,
    mode: str = "service",
) -> Any:
    """
    Singleton factory for the Cerebro Reranker Client.
    Uses lazy import to avoid circular dependencies.
    """
    global _default_client
    if _default_client is None:
        from .rerank_client import CerebroRerankerClient
        _default_client = CerebroRerankerClient(
            service_url=service_url,
            timeout=timeout,
            mode=mode,
        )
    return _default_client


def rerank(
    query: str,
    documents: List[str],
    top_k: Optional[int] = None,
    **kwargs,
) -> List[Tuple[int, float, str]]:
    """
    One‑shot reranking using the hybrid service/local client.
    
    This function now delegates to the CerebroRerankerClient, which
    attempts to use the external service first, falling back to local
    CrossEncoder if necessary.
    """
    # Initialize client (uses defaults or env vars)
    client = get_reranker_client()
    return client.rerank(query, documents, top_k=top_k)
