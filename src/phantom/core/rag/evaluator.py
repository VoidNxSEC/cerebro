"""
cerebro.core.rag.evaluator
───────────────────────────
RAG quality metrics sem ground truth.

O problema de avaliar RAG em produção:
  - Você não tem o "gabarito" (ground truth) para cada query
  - Mas você tem proxies mensuráveis que correlacionam com qualidade

Métricas implementadas (todas sem LLM extra):
  1. answer_relevance:   cosine(query_embed, answer_embed)
                         — resposta fala sobre o que foi perguntado?
  2. context_precision:  fração dos chunks citados na resposta
                         — o modelo usou o contexto que você deu?
  3. rerank_score_top1:  score do cross-encoder no chunk #1
                         — o retrieval foi confiante?
  4. latency_ms:         fim-a-fim
  5. token_efficiency:   tokens_usados / tokens_disponíveis
                         — você está desperdiçando context window?

Para métricas com ground truth (RAGAS), integrar depois com:
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
    Snapshot completo de uma query RAG.
    Persistir isso no dashboard_server → você tem observabilidade real.
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
        Score composto 0-1 sem ground truth.
        Proxy razoável para priorizar investigação de problemas.
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
    Avaliador de qualidade RAG em tempo real (sem ground truth).

    Injeta no pipeline como observer — não bloqueia a resposta.
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
        Calcula métricas para uma query completada.

        Não lança exceção se qualquer métrica falhar —
        degraded metrics > pipeline quebrado.
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
        Fração dos chunks que têm overlap com a resposta.
        Proxy lexical — sem LLM extra.

        Alta precision → modelo usou o contexto recuperado.
        Baixa precision → modelo "alucionou" ou ignorou o contexto.
        """
        if not chunks or not answer:
            return 0.0

        answer_words = set(answer.lower().split())
        used = 0

        for chunk in chunks:
            chunk_words = set(chunk.content.lower().split())
            overlap = len(answer_words & chunk_words) / max(len(chunk_words), 1)
            if overlap > 0.05:  # threshold: 5% das palavras do chunk aparecem na resposta
                used += 1

        return used / len(chunks)

    def _compute_answer_relevance(self, query: str, answer: str) -> float:
        """
        Cosine similarity entre query e answer embeddings.
        Alta relevance → resposta fala sobre o que foi perguntado.
        """
        if not self._embed_system or not answer:
            return 0.0

        try:
            import numpy as np
            q_vec = self._embed_system.embed_query(query)
            a_vec = self._embed_system.embed_query(answer[:512])  # trunca resposta longa

            # Cosine similarity
            q_arr = np.array(q_vec)
            a_arr = np.array(a_vec)
            cos_sim = float(
                np.dot(q_arr, a_arr) /
                (np.linalg.norm(q_arr) * np.linalg.norm(a_arr) + 1e-8)
            )
            return max(0.0, cos_sim)  # clipar negativo
        except Exception as e:
            logger.debug(f"answer_relevance failed: {e}")
            return 0.0

    def get_stats(self, last_n: int = 100) -> dict:
        """Estatísticas agregadas das últimas N queries."""
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
        """Exporta histórico para JSONL — alimenta dashboard ou análise offline."""
        import json
        with open(path, "w") as f:
            for m in self._history:
                f.write(json.dumps(m.to_dict()) + "\n")
        logger.info(f"Exported {len(self._history)} RAG metrics to {path}")
