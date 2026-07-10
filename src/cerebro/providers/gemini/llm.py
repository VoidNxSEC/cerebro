"""
Google Gemini LLM Provider

Implements LLMProvider for the Google Gemini API (Gemini Pro/Flash models).
Uses the google-genai SDK (v1+), which is client-based and does not set
process-global state, so multiple instances with different API keys work.

Env vars:
  GEMINI_API_KEY           Required. Your Google AI API key.
  GEMINI_MODEL             Generation model (default: gemini-1.5-flash)
  GEMINI_EMBEDDING_MODEL   Embedding model (default: models/text-embedding-004)
  GEMINI_TIMEOUT           Request timeout in seconds (default: 120)
"""

import logging
import os
from typing import Any

from cerebro.interfaces.llm import LLMProvider

logger = logging.getLogger("cerebro.providers.gemini")

_DEFAULT_MODEL = "gemini-1.5-flash"
_DEFAULT_EMBEDDING_MODEL = "models/text-embedding-004"
_DEFAULT_TIMEOUT = 120.0


class GeminiProvider(LLMProvider):
    """LLM provider backed by the Google Gemini API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        embedding_model: str | None = None,
        timeout: float | None = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is required. Set it as an environment variable or pass api_key=."
            )
        self.model = model or os.getenv("GEMINI_MODEL", _DEFAULT_MODEL)
        self.embedding_model = embedding_model or os.getenv(
            "GEMINI_EMBEDDING_MODEL", _DEFAULT_EMBEDDING_MODEL
        )
        self.timeout = timeout or float(os.getenv("GEMINI_TIMEOUT", str(_DEFAULT_TIMEOUT)))
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from google import genai
            except ImportError as exc:
                raise ImportError(
                    "The 'google-genai' package is required for GeminiProvider. "
                    "Install it with: poetry install --with gemini"
                ) from exc
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    # ------------------------------------------------------------------
    # Embeddings — Gemini has a native embeddings API
    # ------------------------------------------------------------------

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str], batch_size: int = 20) -> list[list[float]]:
        from google.genai import types

        client = self._get_client()
        results: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            for text in batch:
                response = client.models.embed_content(
                    model=self.embedding_model,
                    contents=text,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
                )
                results.append(list(response.embeddings[0].values))
        return results

    # ------------------------------------------------------------------
    # Text generation
    # ------------------------------------------------------------------

    def generate(self, prompt: str, **kwargs) -> str:
        from google.genai import types

        client = self._get_client()
        config = types.GenerateContentConfig(
            max_output_tokens=kwargs.get("max_tokens", 1024),
            temperature=kwargs.get("temperature", 0.7),
        )
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        return response.text

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
            logger.error("GeminiProvider grounded_generate failed: %s", e)
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
            from google.genai import types

            client = self._get_client()
            client.models.generate_content(
                model=self.model,
                contents="ping",
                config=types.GenerateContentConfig(max_output_tokens=1),
            )
            return True
        except Exception as e:
            logger.warning("GeminiProvider health check failed: %s", e)
            return False
