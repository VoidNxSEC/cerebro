"""
cerebro.core.rag.retriever
───────────────────────────
Hybrid Retrieval with Reciprocal Rank Fusion (RRF).

Dense (semantic) + Sparse (BM25) fused via RRF.
No new infrastructure — rank_bm25 is pure Python.

What this solves in Cerebro:
  - Dense-only misses exact hits: "rerank_client" retrieves poorly if
    the embedding didn't capture the specific technical term
  - BM25-only misses semantics: "how does the reranker work" won't match
    "cross-encoder inference pipeline"
  - Hybrid RRF handles both cases

Usage:
    retriever = HybridRetriever.from_corpus(vector_store, chunks)
    results   = retriever.retrieve("how does the reranker work?", k=5)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Protocol

try:
    from cerebro.core.rag.elasticsearch_store import ElasticsearchStore, ApproxRetrievalStrategy
except ImportError:
    ElasticsearchStore = None
    ApproxRetrievalStrategy = None

logger = logging.getLogger("cerebro.retriever")


# ─── Tipos ───────────────────────────────────────────────────────────────────

@dataclass
class RetrievedChunk:
    id: str
    content: str
    score: float
    metadata: dict
    retrieval_method: str  # "dense", "sparse", "hybrid"


class VectorStoreProtocol(Protocol):
    """Interface mínima esperada do vector store."""
    def similarity_search_with_score(
        self, query: str, k: int, filter: dict | None = None
    ) -> list[tuple[Any, float]]: ...


# ─── BM25 com fallback gracioso ──────────────────────────────────────────────

class _BM25Wrapper:
    """
    Wrapper que tenta usar rank_bm25 e faz fallback para
    TF-IDF manual se não estiver no nix shell ainda.
    """

    def __init__(self, corpus: list[str]):
        self.corpus = corpus
        self._impl = self._init_bm25(corpus)

    def _init_bm25(self, corpus):
        try:
            from rank_bm25 import BM25Okapi
            tokenized = [doc.lower().split() for doc in corpus]
            logger.debug(f"BM25Okapi inicializado com {len(corpus)} documentos")
            return BM25Okapi(tokenized)
        except ImportError:
            logger.warning(
                "rank_bm25 não disponível — usando TF-IDF fallback. "
                "Adicione 'rank-bm25' ao flake.nix para melhor sparse retrieval."
            )
            return _TFIDFFallback(corpus)

    def get_scores(self, query: str) -> list[float]:
        tokenized_query = query.lower().split()
        return self._impl.get_scores(tokenized_query)


class _TFIDFFallback:
    """
    TF-IDF manual mínimo — funciona sem deps extras.
    Inferior ao BM25 mas melhor que nothing.
    """

    def __init__(self, corpus: list[str]):
        import math
        self.corpus = corpus
        self.n = len(corpus)
        tokenized = [doc.lower().split() for doc in corpus]

        # IDF
        df: dict[str, int] = {}
        for doc in tokenized:
            for term in set(doc):
                df[term] = df.get(term, 0) + 1
        self.idf = {
            term: math.log((self.n + 1) / (freq + 1)) + 1
            for term, freq in df.items()
        }
        self.tokenized = tokenized

    def get_scores(self, query: list[str]) -> list[float]:
        scores = []
        for doc_tokens in self.tokenized:
            doc_len = len(doc_tokens)
            score = 0.0
            for term in query:
                tf = doc_tokens.count(term) / max(doc_len, 1)
                idf = self.idf.get(term, 0.0)
                score += tf * idf
            scores.append(score)
        return scores


# ─── Hybrid Retriever ────────────────────────────────────────────────────────

class HybridRetriever:
    """
    RRF fusion: dense (ChromaDB/Vertex) + sparse (BM25).

    Parâmetros:
        alpha:    peso do dense (0.0 = só sparse, 1.0 = só dense)
                  0.6 é um bom default para code search
        k_fetch:  quantos docs buscar em cada retriever antes do RRF
                  busca generosa, reranker filtra depois
        rrf_k:    parâmetro de smoothing do RRF (60 é padrão na literatura)
    """

    def __init__(
        self,
        vector_store: VectorStoreProtocol,
        corpus_texts: list[str],
        corpus_ids: list[str],
        corpus_metadata: list[dict],
        alpha: float = 0.6,
        k_fetch: int = 20,
        rrf_k: int = 60,
    ):
        self.vector_store   = vector_store
        self.corpus_texts   = corpus_texts
        self.corpus_ids     = corpus_ids
        self.corpus_meta    = corpus_metadata
        self.alpha          = alpha
        self.k_fetch        = k_fetch
        self.rrf_k          = rrf_k
        self._bm25          = _BM25Wrapper(corpus_texts)

    @classmethod
    def from_corpus(
        cls,
        vector_store: VectorStoreProtocol,
        chunks: list,  # list[Chunk] do chunker.py
        **kwargs,
    ) -> HybridRetriever:
        """Convenience constructor a partir de Chunk objects."""
        texts    = [c.content for c in chunks]
        ids      = [c.id for c in chunks]
        metadata = [c.to_dict() for c in chunks]
        return cls(vector_store, texts, ids, metadata, **kwargs)

    @classmethod
    def from_elasticsearch(
        cls,
        index_name: str,
        embedding: Any,
        chunks: list,
        es_url: str | None = None,
        es_cloud_id: str | None = None,
        es_user: str | None = None,
        es_password: str | None = None,
        es_api_key: str | None = None,
        **kwargs,
    ) -> HybridRetriever:
        """Convenience constructor from standard Elasticsearch setup.
        Will use ElasticsearchStore as the Dense provider within the Hybrid/RRF ecosystem.
        """
        if ElasticsearchStore is None:
            raise ImportError(
                "ElasticsearchStore not available. Certifique-se que as dependências do gcp/elasticsearch estão instaladas."
            )
        
        # Instanciando a estratégia Híbrida com RRF Nativo
        strategy = None
        if ApproxRetrievalStrategy is not None:
            strategy = ApproxRetrievalStrategy(
                hybrid=True, # Ativa BM25 + Vetor simultaneamente
                rrf=True     # Aplica o Reciprocal Rank Fusion na própria query
            )

        vector_store = ElasticsearchStore(
            index_name=index_name,
            embedding=embedding,
            es_url=es_url,
            es_cloud_id=es_cloud_id,
            es_user=es_user,
            es_password=es_password,
            es_api_key=es_api_key,
            strategy=strategy,
        )
        return cls.from_corpus(vector_store, chunks, **kwargs)

    def retrieve(
        self,
        query: str,
        k: int = 5,
        filters: dict | None = None,
    ) -> list[RetrievedChunk]:
        """
        Pipeline completo: dense + sparse → RRF → top-k.

        Args:
            query:   texto da query (já expandido se usar QueryExpander)
            k:       número de resultados finais
            filters: metadata filters (ex: {"language": "python", "repo": "cerebro"})
        """
        t0 = time.time()

        # 1. Dense retrieval
        dense_results = self._dense_retrieve(query, filters)

        # 2. Sparse retrieval (BM25)
        sparse_results = self._sparse_retrieve(query)

        # 3. RRF fusion
        fused = self._rrf_fusion(dense_results, sparse_results)

        # 4. Top-k
        top_k = fused[:k]

        latency = (time.time() - t0) * 1000
        logger.info(
            "hybrid_retrieve",
            extra={
                "query_preview": query[:60],
                "dense_hits":    len(dense_results),
                "sparse_hits":   len(sparse_results),
                "k_requested":   k,
                "k_returned":    len(top_k),
                "latency_ms":    round(latency, 2),
            }
        )

        return top_k

    def _dense_retrieve(
        self,
        query: str,
        filters: dict | None,
    ) -> list[tuple[str, float]]:
        """Retorna lista de (doc_id, score) do vector store."""
        try:
            results = self.vector_store.similarity_search_with_score(
                query, k=self.k_fetch, filter=filters
            )
            # Normaliza para (id, score) independente de provider
            normalized = []
            for doc, score in results:
                doc_id = getattr(doc, "id", None) or doc.metadata.get("id", "")
                normalized.append((doc_id, float(score)))
            return normalized
        except Exception as e:
            logger.warning(f"Dense retrieval failed: {e} — usando só sparse")
            return []

    def _sparse_retrieve(self, query: str) -> list[tuple[str, float]]:
        """Retorna lista de (doc_id, bm25_score)."""
        scores = self._bm25.get_scores(query)
        indexed = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )[:self.k_fetch]
        return [
            (self.corpus_ids[i], score)
            for i, score in indexed
            if score > 0
        ]

    def _rrf_fusion(
        self,
        dense: list[tuple[str, float]],
        sparse: list[tuple[str, float]],
    ) -> list[RetrievedChunk]:
        """
        Reciprocal Rank Fusion.

        Score(d) = α * (1 / (k + rank_dense(d))) +
                   (1-α) * (1 / (k + rank_sparse(d)))

        Docs que aparecem em ambos os rankings ganham boost.
        """
        rrf_scores: dict[str, float] = {}

        for rank, (doc_id, _) in enumerate(dense):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0)
            rrf_scores[doc_id] += self.alpha * (1.0 / (self.rrf_k + rank + 1))

        for rank, (doc_id, _) in enumerate(sparse):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0)
            rrf_scores[doc_id] += (1 - self.alpha) * (1.0 / (self.rrf_k + rank + 1))

        # Monta RetrievedChunk objects
        results = []
        for doc_id, score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
            idx = self._find_corpus_idx(doc_id)
            if idx is None:
                continue
            results.append(RetrievedChunk(
                id=doc_id,
                content=self.corpus_texts[idx],
                score=score,
                metadata=self.corpus_meta[idx],
                retrieval_method="hybrid",
            ))

        return results

    def _find_corpus_idx(self, doc_id: str) -> int | None:
        try:
            return self.corpus_ids.index(doc_id)
        except ValueError:
            return None

    def update_corpus(self, new_chunks: list) -> None:
        """
        Atualiza o corpus BM25 sem recriar o retriever inteiro.
        Útil quando novos repositórios são ingeridos em runtime.
        """
        self.corpus_texts   = [c.content for c in new_chunks]
        self.corpus_ids     = [c.id for c in new_chunks]
        self.corpus_meta    = [c.to_dict() for c in new_chunks]
        self._bm25          = _BM25Wrapper(self.corpus_texts)
        logger.info(f"Corpus atualizado: {len(new_chunks)} chunks")
