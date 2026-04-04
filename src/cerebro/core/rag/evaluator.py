"""
cerebro.core.rag.evaluator
───────────────────────────
RAG quality metrics without ground truth.

The challenge of evaluating RAG in production:
  - You don't have the "answer key" (ground truth) for each query
  - But you have measurable proxies that correlate with quality

Implemented metrics (all without extra LLM calls):
  1. answer_relevance:   cosine(query_embed, answer_embed)
                         — does the answer address what was asked?
  2. context_precision:  fraction of chunks cited in the answer
                         — did the model use the context it was given?
  3. rerank_score_top1:  cross-encoder score for chunk #1
                         — was the retrieval confident?
  4. latency_ms:         end-to-end
  5. token_efficiency:   tokens_used / tokens_available
                         — is context window being wasted?

For ground-truth metrics (RAGAS), integrate later with:
  pip install ragas
  → faithfulness, answer_correctness, context_recall
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger("cerebro.evaluator")


@dataclass
class RAGMetrics:
    """
    Complete snapshot of a RAG query.
    Persist this to the dashboard server for real observability.
    """
    # Query
    query:              str
    query_expanded:     str | None = None

    # Retrieval
    retrieval_k:        int   = 0
    retrieval_method:   str   = "hybrid"
    rerank_score_top1:  float = 0.0
    rerank_score_mean:  float = 0.0

    # Context
    context_tokens:     int   = 0
    chunks_used:        int   = 0
    chunks_dropped:     int   = 0
    context_precision:  float = 0.0   # 0.0 a 1.0

    # Generation
    generation_tokens:  int   = 0
    model_used:         str   = ""
    answer_relevance:   float = 0.0   # cosine similarity, 0.0 a 1.0

    # Latency breakdown (ms)
    latency_retrieval:  float = 0.0
    latency_rerank:     float = 0.0
    latency_generation: float = 0.0
    latency_total:      float = 0.0

    # Efficiency
    token_efficiency:   float = 0.0   # context_tokens / token_budget

    # Timestamp
    timestamp:          float = field(default_factory=time.time)

    @property
    def quality_score(self) -> float:
        """
        Composite score 0-1 without ground truth.
        Reasonable proxy for prioritizing problem investigation.
        """
        weights = {
            "answer_relevance":  0.40,
            "context_precision": 0.30,
            "rerank_score_top1": 0.20,
            "token_efficiency":  0.10,
        }
        return sum(
            getattr(self, metric) * weight
            for metric, weight in weights.items()
        )

    def to_dict(self) -> dict:
        return {
            "query":              self.query[:100],
            "retrieval_k":        self.retrieval_k,
            "retrieval_method":   self.retrieval_method,
            "rerank_score_top1":  round(self.rerank_score_top1, 4),
            "context_tokens":     self.context_tokens,
            "chunks_used":        self.chunks_used,
            "context_precision":  round(self.context_precision, 4),
            "generation_tokens":  self.generation_tokens,
            "answer_relevance":   round(self.answer_relevance, 4),
            "latency_total_ms":   round(self.latency_total, 2),
            "quality_score":      round(self.quality_score, 4),
            "timestamp":          self.timestamp,
        }


class RAGEvaluator:
    """
    Real-time RAG quality evaluator (without ground truth).

    Injected into the pipeline as an observer — does not block the response.
    """

    def __init__(self, embedding_system=None):
        self._embed_system = embedding_system
        self._history: list[RAGMetrics] = []

    def evaluate(
        self,
        query: str,
        answer: str,
        retrieved_chunks: list,
        rerank_scores: list[float] | None = None,
        timing: dict | None = None,
        model_used: str = "",
        context_budget: int = 16_000,
    ) -> RAGMetrics:
        """
        Compute metrics for a completed query.

        Does not raise if any individual metric fails —
        degraded metrics > broken pipeline.
        """
        metrics = RAGMetrics(
            query=query,
            retrieval_k=len(retrieved_chunks),
            model_used=model_used,
        )

        # Timing
        if timing:
            metrics.latency_retrieval  = timing.get("retrieval", 0.0)
            metrics.latency_rerank     = timing.get("rerank", 0.0)
            metrics.latency_generation = timing.get("generation", 0.0)
            metrics.latency_total      = timing.get("total", 0.0)

        # Rerank scores
        if rerank_scores:
            metrics.rerank_score_top1 = rerank_scores[0] if rerank_scores else 0.0
            metrics.rerank_score_mean = sum(rerank_scores) / len(rerank_scores)

        # Context stats
        context_text = " ".join(c.content for c in retrieved_chunks)
        metrics.context_tokens  = len(context_text) // 4
        metrics.chunks_used     = len(retrieved_chunks)
        metrics.token_efficiency = min(metrics.context_tokens / max(context_budget, 1), 1.0)

        # Context precision (lexical proxy)
        metrics.context_precision = self._compute_context_precision(answer, retrieved_chunks)

        # Answer relevance (embedding cosine se disponível)
        metrics.answer_relevance = self._compute_answer_relevance(query, answer)

        self._history.append(metrics)

        logger.info(
            "rag_evaluated",
            extra={
                "quality_score":   round(metrics.quality_score, 3),
                "answer_relevance": round(metrics.answer_relevance, 3),
                "latency_ms":      round(metrics.latency_total, 1),
            }
        )

        return metrics

    def _compute_context_precision(self, answer: str, chunks: list) -> float:
        """
        Fraction of chunks with lexical overlap in the answer.
        Lexical proxy — no extra LLM call needed.

        High precision → model used the retrieved context.
        Low precision → model hallucinated or ignored context.
        """
        if not chunks or not answer:
            return 0.0

        answer_words = set(answer.lower().split())
        used = 0

        for chunk in chunks:
            chunk_words = set(chunk.content.lower().split())
            overlap = len(answer_words & chunk_words) / max(len(chunk_words), 1)
            if overlap > 0.05:  # threshold: 5% of chunk words appear in the answer
                used += 1

        return used / len(chunks)

    def _compute_answer_relevance(self, query: str, answer: str) -> float:
        """
        Cosine similarity between query and answer embeddings.
        High relevance → answer addresses what was asked.
        """
        if not self._embed_system or not answer:
            return 0.0

        try:
            import numpy as np
            q_vec = self._embed_system.embed_query(query)
            a_vec = self._embed_system.embed_query(answer[:512])  # truncate long answers

            # Cosine similarity
            q_arr = np.array(q_vec)
            a_arr = np.array(a_vec)
            cos_sim = float(
                np.dot(q_arr, a_arr) /
                (np.linalg.norm(q_arr) * np.linalg.norm(a_arr) + 1e-8)
            )
            return max(0.0, cos_sim)  # clip negative values
        except Exception as e:
            logger.debug(f"answer_relevance failed: {e}")
            return 0.0

    def get_stats(self, last_n: int = 100) -> dict:
        """Aggregated statistics for the last N queries."""
        recent = self._history[-last_n:]
        if not recent:
            return {}

        return {
            "n_queries":           len(recent),
            "avg_quality":         sum(m.quality_score for m in recent) / len(recent),
            "avg_latency_ms":      sum(m.latency_total for m in recent) / len(recent),
            "avg_answer_relevance": sum(m.answer_relevance for m in recent) / len(recent),
            "avg_context_precision": sum(m.context_precision for m in recent) / len(recent),
            "p95_latency_ms":      sorted(m.latency_total for m in recent)[int(len(recent) * 0.95)],
        }

    def export_jsonl(self, path: str):
        """Export history to JSONL — feeds the dashboard or offline analysis."""
        import json
        with open(path, "w") as f:
            for m in self._history:
                f.write(json.dumps(m.to_dict()) + "\n")
        logger.info(f"Exported {len(self._history)} RAG metrics to {path}")
