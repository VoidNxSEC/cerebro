"""
cerebro.core.rag.orchestrator
──────────────────────────────
Orchestration layer — o maestro do RAG pipeline.

Responsabilidades:
  1. Cache de queries (evita re-processar queries idênticas)
  2. Query expansion (HyDE opcional)
  3. Routing: local (ChromaDB) vs cloud (Vertex AI)
  4. Composição: retriever → reranker → context_manager → LLM
  5. Métricas via RAGEvaluator

Este é o entry point que o engine.py deveria ter —
substitui a lógica ad-hoc espalhada em RigorousRAGEngine.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger("cerebro.orchestrator")


@dataclass
class OrchestratorConfig:
    """Configuração completa do pipeline RAG."""
    # Retrieval
    retrieval_k:     int   = 20       # busca generosa, reranker filtra
    final_k:         int   = 5        # results após rerank
    alpha:           float = 0.6      # peso dense no RRF

    # Context
    model:           str   = "claude-sonnet-4"
    context_strategy: str  = "reorder"

    # Cache
    cache_ttl:       int   = 3600     # segundos (1h)
    cache_max_size:  int   = 512      # queries em memória

    # Features
    use_hybrid:      bool  = True     # RRF fusion
    use_reranker:    bool  = True     # cross-encoder rerank
    use_evaluator:   bool  = True     # RAG metrics
    query_expansion: bool  = False    # HyDE (phase 2)

    # Routing
    prefer_local:    bool  = True     # True = ChromaDB first


@dataclass
class RAGResponse:
    """Resposta completa do pipeline RAG."""
    answer: str
    sources: list[dict]        # chunks citados com metadata
    query: str
    latency_ms: float
    from_cache: bool = False
    metrics: dict | None = None


class QueryCache:
    """
    LRU cache in-memory para queries RAG.
    Sem Redis nem deps externas — dict com TTL manual.
    Em produção, trocar por Redis com uma linha.
    """

    def __init__(self, max_size: int = 512, ttl: int = 3600):
        self._cache: dict[str, tuple[RAGResponse, float]] = {}
        self.max_size = max_size
        self.ttl      = ttl
        self._hits    = 0
        self._misses  = 0

    def _key(self, query: str, filters: dict | None = None) -> str:
        content = f"{query}:{filters or {}}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get(self, query: str, filters: dict | None = None) -> RAGResponse | None:
        key = self._key(query, filters)
        if key in self._cache:
            response, ts = self._cache[key]
            if time.time() - ts < self.ttl:
                self._hits += 1
                logger.debug(f"Cache HIT: {query[:50]}")
                return response
            else:
                del self._cache[key]
        self._misses += 1
        return None

    def set(self, query: str, response: RAGResponse, filters: dict | None = None):
        if len(self._cache) >= self.max_size:
            # Evict oldest
            oldest = min(self._cache.items(), key=lambda x: x[1][1])
            del self._cache[oldest[0]]
        key = self._key(query, filters)
        self._cache[key] = (response, time.time())

    def invalidate(self):
        self._cache.clear()
        logger.info("Query cache invalidated")

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def stats(self) -> dict:
        return {
            "size":     len(self._cache),
            "max_size": self.max_size,
            "hits":     self._hits,
            "misses":   self._misses,
            "hit_rate": round(self.hit_rate, 3),
            "ttl_s":    self.ttl,
        }


class RAGOrchestrator:
    """
    Orquestra o pipeline RAG completo.

    Injetável — aceita qualquer implementação de retriever, reranker, LLM.
    Compatível com os providers existentes em phantom/providers/.

    Usage:
        orchestrator = RAGOrchestrator(
            retriever=hybrid_retriever,
            reranker=rerank_client,
            llm=llm_provider,
            config=OrchestratorConfig(),
        )
        response = orchestrator.query("como funciona o reranker?")
    """

    def __init__(
        self,
        retriever,          # HybridRetriever ou qualquer retriever com .retrieve()
        llm,                # LLMProvider (interface existente em phantom/interfaces/)
        reranker=None,      # RerankClient (opcional)
        evaluator=None,     # RAGEvaluator (opcional)
        config: OrchestratorConfig | None = None,
    ):
        self.retriever  = retriever
        self.llm        = llm
        self.reranker   = reranker
        self.evaluator  = evaluator
        self.config     = config or OrchestratorConfig()
        self._cache     = QueryCache(
            max_size=self.config.cache_max_size,
            ttl=self.config.cache_ttl,
        )

        from cerebro.core.rag.context_manager import ContextManager
        self._ctx_manager = ContextManager(
            model=self.config.model,
            strategy=self.config.context_strategy,
        )

    def query(
        self,
        query: str,
        filters: dict | None = None,
        skip_cache: bool = False,
    ) -> RAGResponse:
        """
        Pipeline completo: cache → retrieve → rerank → compress → generate.

        Args:
            query:      pergunta do usuário
            filters:    metadata filters (repo, language, etc.)
            skip_cache: força re-processamento mesmo com cache hit
        """
        t_start = time.time()
        timing  = {}

        # 1. Cache check
        if not skip_cache:
            cached = self._cache.get(query, filters)
            if cached:
                cached.from_cache = True
                return cached

        # 2. Query expansion (HyDE — phase 2)
        effective_query = query
        if self.config.query_expansion:
            effective_query = self._expand_query(query)

        # 3. Retrieval
        t_r = time.time()
        chunks = self.retriever.retrieve(
            effective_query,
            k=self.config.retrieval_k,
            filters=filters,
        )
        timing["retrieval"] = (time.time() - t_r) * 1000

        if not chunks:
            logger.warning(f"Zero chunks retrieved for: {query[:60]}")
            return RAGResponse(
                answer="Não encontrei informações relevantes no corpus indexado.",
                sources=[],
                query=query,
                latency_ms=(time.time() - t_start) * 1000,
            )

        # 4. Reranking
        rerank_scores = []
        t_rr = time.time()
        if self.reranker and self.config.use_reranker:
            try:
                reranked = self.reranker.rerank(query, chunks, top_k=self.config.final_k)
                rerank_scores = [getattr(c, 'score', 0.0) for c in reranked]
                chunks = reranked
            except Exception as e:
                logger.warning(f"Reranker failed: {e} — usando retrieval order")
                chunks = chunks[:self.config.final_k]
        else:
            chunks = chunks[:self.config.final_k]
        timing["rerank"] = (time.time() - t_rr) * 1000

        # 5. Context preparation
        prepared = self._ctx_manager.prepare(effective_query, chunks)

        # 6. Generation
        t_g = time.time()
        answer = self._generate(query, prepared.text)
        timing["generation"] = (time.time() - t_g) * 1000
        timing["total"]      = (time.time() - t_start) * 1000

        # 7. Build sources list
        sources = [
            {
                "id":      getattr(c, 'id', ''),
                "content": c.content[:200],  # preview
                "score":   getattr(c, 'score', 0.0),
                **getattr(c, 'metadata', {}),
            }
            for c in chunks
        ]

        response = RAGResponse(
            answer=answer,
            sources=sources,
            query=query,
            latency_ms=timing["total"],
        )

        # 8. Evaluation (non-blocking)
        if self.evaluator and self.config.use_evaluator:
            try:
                metrics = self.evaluator.evaluate(
                    query=query,
                    answer=answer,
                    retrieved_chunks=chunks,
                    rerank_scores=rerank_scores,
                    timing=timing,
                    model_used=self.config.model,
                )
                response.metrics = metrics.to_dict()
            except Exception as e:
                logger.debug(f"Evaluator failed (non-critical): {e}")

        # 9. Cache store
        if not skip_cache:
            self._cache.set(query, response, filters)

        logger.info(
            "query_completed",
            extra={
                "latency_ms":  round(timing["total"], 1),
                "chunks_used": len(chunks),
                "from_cache":  False,
            }
        )

        return response

    def _generate(self, query: str, context: str) -> str:
        """Geração com contexto — compatível com LLMProvider interface."""
        prompt = self._build_prompt(query, context)
        try:
            return self.llm.generate(prompt)
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"Erro na geração: {type(e).__name__}"

    def _build_prompt(self, query: str, context: str) -> str:
        return f"""You are Cerebro, an expert code intelligence assistant.
Answer the question based ONLY on the provided context.
If the context doesn't contain enough information, say so explicitly.
Always cite your sources using the [N] notation.

Context:
{context}

Question: {query}

Answer:"""

    def _expand_query(self, query: str) -> str:
        """
        HyDE (Hypothetical Document Embeddings) — phase 2.
        Gera uma resposta hipotética e usa ela para melhorar retrieval.
        Por ora, retorna a query original.
        """
        logger.debug("Query expansion (HyDE) not yet implemented — using original query")
        return query

    @property
    def cache_stats(self) -> dict:
        return self._cache.stats

    def invalidate_cache(self):
        self._cache.invalidate()
