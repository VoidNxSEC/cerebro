"""
Groq LLM Provider

Implements LLMProvider for the Groq API (ultra-fast open model inference).
Embeddings are NOT supported by the Groq API — the engine's local
EmbeddingSystem handles that automatically for this provider.

Env vars:
  GROQ_API_KEY   Required. Your Groq API key.
  GROQ_MODEL     Model to use (default: llama-3.3-70b-versatile)
  GROQ_TIMEOUT   Request timeout in seconds (default: 120)
"""

import logging
import os
from typing import Any

from cerebro.interfaces.llm import LLMProvider

logger = logging.getLogger("cerebro.providers.groq")

_DEFAULT_MODEL = "llama-3.3-70b-versatile"
_DEFAULT_TIMEOUT = 120.0


class GroqProvider(LLMProvider):
    """LLM provider backed by the Groq API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is required. Set it as an environment variable or pass api_key=."
            )
        self.model = model or os.getenv("GROQ_MODEL", _DEFAULT_MODEL)
        self.timeout = timeout or float(os.getenv("GROQ_TIMEOUT", str(_DEFAULT_TIMEOUT)))
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import groq
            except ImportError as exc:
                raise ImportError(
                    "The 'groq' package is required for GroqProvider. "
                    "Install it with: poetry install --with groq"
                ) from exc
            self._client = groq.Groq(api_key=self.api_key)
        return self._client

    # ------------------------------------------------------------------
    # Embeddings — not available from Groq; engine uses EmbeddingSystem
    # ------------------------------------------------------------------

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError(
            "Groq has no embeddings API. "
            "The EmbeddingSystem handles embeddings automatically for this provider."
        )

    def embed_batch(self, texts: list[str], batch_size: int = 20) -> list[list[float]]:
        raise NotImplementedError(
            "Groq has no embeddings API. "
            "The EmbeddingSystem handles embeddings automatically for this provider."
        )

    # ------------------------------------------------------------------
    # Text generation
    # ------------------------------------------------------------------

    def generate(self, prompt: str, **kwargs) -> str:
        response = self._get_client().chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", 1024),
            temperature=kwargs.get("temperature", 0.7),
        )
        return response.choices[0].message.content

    def grounded_generate(
        self,
        query: str,
        context: list[str],
        top_k: int = 5,
        **kwargs,
    ) -> dict[str, Any]:
        ctx_text = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(context[:top_k]))
        prompt = (
            "Answer the following question based only on the provided context.\n\n"
            f"Context:\n{ctx_text}\n\n"
            f"Question: {query}\n\n"
            "Answer:"
        )
        try:
            answer = self.generate(prompt, **kwargs)
            return {
                "answer": answer,
                "citations": [f"[{i + 1}]" for i in range(min(top_k, len(context)))],
                "snippets": context[:top_k],
                "confidence": 0.9,
                "cost_estimate": 0.0,
            }
        except Exception as e:
            logger.error("GroqProvider grounded_generate failed: %s", e)
            return {
                "answer": f"Error: {e}",
                "citations": [],
                "snippets": [],
                "confidence": 0.0,
                "cost_estimate": 0.0,
            }

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        try:
            self._get_client().models.list()
            return True
        except Exception as e:
            logger.warning("GroqProvider health check failed: %s", e)
            return False
