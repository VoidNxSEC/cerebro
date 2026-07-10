"""
cerebro.core.rag.context_manager
──────────────────────────────────
Context compression e reordenação para mitigar "lost-in-the-middle".

O problema:
    LLMs tendem a lembrar melhor o início e o fim do contexto.
    Chunks relevantes no meio se perdem.
    Paper: "Lost in the Middle" (Liu et al., 2023)

A solução implementada aqui:
    1. Reordena chunks: mais relevante primeiro e último
    2. Trunca para o budget do modelo
    3. Comprime context se necessário (extrai sentenças-chave)

Usage:
    cm = ContextManager(model="claude-opus")
    context_str = cm.prepare(query, retrieved_chunks)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("cerebro.context_manager")

# Estimativas de token budget por modelo
# 60% do context window reservado para o contexto RAG
_MODEL_BUDGETS: dict[str, int] = {
    "claude-opus-4":        int(200_000 * 0.60),
    "claude-sonnet-4":      int(200_000 * 0.60),
    "claude-haiku-4":       int(200_000 * 0.60),
    "gemini-1.5-pro":       int(128_000 * 0.60),
    "gemini-1.5-flash":     int(128_000 * 0.60),
    "mistral-7b":           int(32_000  * 0.60),
    "default":              int(16_000  * 0.60),
}


@dataclass
class PreparedContext:
    """Resultado do context preparation — pronto para injetar no prompt."""
    text: str
    chunks_used: int
    chunks_dropped: int
    token_estimate: int
    strategy_applied: str


class ContextManager:
    """
    Prepara o contexto RAG para injeção no prompt de geração.

    Estratégias disponíveis:
        "reorder"    — Lost-in-the-middle mitigation (default)
        "truncate"   — Simples truncagem por token limit
        "compress"   — Extrai sentenças mais relevantes (experimental)
    """

    def __init__(
        self,
        model: str = "default",
        strategy: str = "reorder",
        add_metadata: bool = True,
    ):
        self.token_budget  = _MODEL_BUDGETS.get(model, _MODEL_BUDGETS["default"])
        self.strategy      = strategy
        self.add_metadata  = add_metadata
        self.model         = model

    def prepare(
        self,
        query: str,
        chunks: list,  # list[RetrievedChunk] do retriever.py
        max_chunks: int = 10,
    ) -> PreparedContext:
        """
        Pipeline principal de context preparation.

        1. Limita ao max_chunks
        2. Aplica estratégia de reordenação
        3. Trunca para token budget
        4. Formata para injeção no prompt
        """
        if not chunks:
            return PreparedContext(
                text="No context available.",
                chunks_used=0,
                chunks_dropped=0,
                token_estimate=0,
                strategy_applied="empty",
            )

        # Limita quantidade inicial
        candidates = chunks[:max_chunks]

        # Aplica estratégia
        if self.strategy == "reorder":
            ordered = self._reorder_lost_in_middle(candidates)
            strategy_name = "reorder"
        elif self.strategy == "compress":
            ordered = self._compress_chunks(query, candidates)
            strategy_name = "compress"
        else:
            ordered = candidates
            strategy_name = "truncate"

        # Trunca para token budget
        selected, dropped = self._truncate_to_budget(ordered)

        # Formata
        text = self._format_context(selected)
        token_est = len(text) // 4

        logger.info(
            "context_prepared",
            extra={
                "model":           self.model,
                "strategy":        strategy_name,
                "chunks_used":     len(selected),
                "chunks_dropped":  dropped,
                "token_estimate":  token_est,
                "budget":          self.token_budget,
            }
        )

        return PreparedContext(
            text=text,
            chunks_used=len(selected),
            chunks_dropped=dropped,
            token_estimate=token_est,
            strategy_applied=strategy_name,
        )

    def _reorder_lost_in_middle(self, chunks: list) -> list:
        """
        Reordenação para mitigar lost-in-the-middle.

        Dado N chunks ordenados por relevância [0..N-1]:
        Resultado: [0, 2, 4, ..., 5, 3, 1]
        Mais relevante no início, segundo mais relevante no fim,
        menos relevantes no meio.

        Isso explora o viés de attention do transformer:
        tokens no início e no fim têm maior peso.
        """
        if len(chunks) <= 2:
            return chunks

        result = []
        left  = 0
        right = len(chunks) - 1
        toggle = True

        while left <= right:
            if toggle:
                result.append(chunks[left])
                left += 1
            else:
                result.append(chunks[right])
                right -= 1
            toggle = not toggle

        return result

    def _compress_chunks(self, query: str, chunks: list) -> list:
        """
        Compressão básica: extrai sentenças que contêm termos da query.
        Reduz chunks longos mantendo as partes mais relevantes.

        Não usa LLM extra — compressão puramente lexical.
        Para compressão semântica real, usar LLMLingua (phase 3).
        """
        query_terms = set(query.lower().split())
        compressed = []

        for chunk in chunks:
            sentences = chunk.content.split(". ")
            relevant = [
                s for s in sentences
                if any(term in s.lower() for term in query_terms)
            ]
            if relevant:
                # Cria cópia com conteúdo comprimido
                import copy
                compressed_chunk = copy.copy(chunk)
                compressed_chunk.content = ". ".join(relevant[:5])  # max 5 sentenças
                compressed.append(compressed_chunk)
            else:
                compressed.append(chunk)

        return compressed

    def _truncate_to_budget(self, chunks: list) -> tuple[list, int]:
        """
        Seleciona chunks que cabem no token budget.
        Trunca conteúdo do último chunk se necessário.
        """
        selected = []
        tokens_used = 0
        dropped = 0

        for chunk in chunks:
            chunk_tokens = len(chunk.content) // 4
            if tokens_used + chunk_tokens <= self.token_budget:
                selected.append(chunk)
                tokens_used += chunk_tokens
            else:
                # Tenta incluir parcialmente o último chunk
                remaining_tokens = self.token_budget - tokens_used
                if remaining_tokens > 100:  # mínimo para ser útil
                    import copy
                    partial = copy.copy(chunk)
                    partial.content = chunk.content[:remaining_tokens * 4]
                    selected.append(partial)
                dropped += 1

        return selected, dropped

    def _format_context(self, chunks: list) -> str:
        """
        Formata chunks para injeção no prompt.
        Inclui metadata como source references para grounded generation.
        """
        parts = []

        for i, chunk in enumerate(chunks, 1):
            meta = getattr(chunk, 'metadata', {})

            if self.add_metadata:
                source = self._format_source(meta)
                header = f"[{i}] {source}"
            else:
                header = f"[{i}]"

            parts.append(f"{header}\n{chunk.content}")

        return "\n\n---\n\n".join(parts)

    def _format_source(self, metadata: dict) -> str:
        """Formata source reference para citação."""
        parts = []
        if repo := metadata.get("repo"):
            parts.append(repo)
        if file := metadata.get("file"):
            # Pega apenas o caminho relativo curto
            parts.append(file.split("/")[-1])
        if line := metadata.get("line_start"):
            parts.append(f"L{line}")
        if name := metadata.get("name"):
            parts.append(f"({name})")
        return " · ".join(parts) if parts else "unknown source"
