"""
Anthropic Claude LLM Provider

Implements LLMProvider for the Anthropic API (Claude models).
Embeddings are NOT supported by the Anthropic API — the engine's local
EmbeddingSystem handles that automatically for this provider.

Env vars:
  ANTHROPIC_API_KEY   Required. Your Anthropic API key.
  ANTHROPIC_MODEL     Model to use (default: claude-sonnet-4-6)
  ANTHROPIC_TIMEOUT   Request timeout in seconds (default: 120)
"""

import logging
import os
from typing import Any

from cerebro.interfaces.llm import LLMProvider

logger = logging.getLogger("cerebro.providers.anthropic")

_DEFAULT_MODEL = "claude-sonnet-4-6"
_DEFAULT_TIMEOUT = 120.0


class AnthropicProvider(LLMProvider):
    """LLM provider backed by the Anthropic API (Claude models)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. Set it as an environment variable or pass api_key=."
            )
        self.model = model or os.getenv("ANTHROPIC_MODEL", _DEFAULT_MODEL)
        self.timeout = timeout or float(os.getenv("ANTHROPIC_TIMEOUT", str(_DEFAULT_TIMEOUT)))
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as exc:
                raise ImportError(
                    "The 'anthropic' package is required for AnthropicProvider. "
                    "Install it with: poetry install --with anthropic"
                ) from exc
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    # ------------------------------------------------------------------
    # Embeddings — not available from Anthropic; engine uses EmbeddingSystem
    # ------------------------------------------------------------------

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError(
            "Anthropic has no embeddings API. "
            "The EmbeddingSystem handles embeddings automatically for this provider."
        )

    def embed_batch(self, texts: list[str], batch_size: int = 20) -> list[list[float]]:
        raise NotImplementedError(
            "Anthropic has no embeddings API. "
            "The EmbeddingSystem handles embeddings automatically for this provider."
        )

    # ------------------------------------------------------------------
    # Text generation
    # ------------------------------------------------------------------

    def generate(self, prompt: str, **kwargs) -> str:
        response = self._get_client().messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1024),
            temperature=kwargs.get("temperature", 0.7),
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

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
            logger.error("AnthropicProvider grounded_generate failed: %s", e)
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
            logger.warning("AnthropicProvider health check failed: %s", e)
            return False
