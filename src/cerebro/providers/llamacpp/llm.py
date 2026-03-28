"""
LlamaCpp LLM Provider

Implements LLMProvider interface for a local llama.cpp server.
The server must expose an OpenAI-compatible API (llama-server --port 8081).

Env vars:
  LLAMA_CPP_URL   Base URL of the llama.cpp server (default: http://localhost:8081)
  LLAMA_CPP_MODEL Model name to pass in requests (default: local)
"""

import logging
import os
from typing import Any

import httpx

from cerebro.interfaces.llm import LLMProvider

logger = logging.getLogger("cerebro.providers.llamacpp")

_DEFAULT_URL = "http://localhost:8081"


class LlamaCppProvider(LLMProvider):
    """LLM provider backed by a local llama.cpp server (OpenAI-compatible API)."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ):
        self.base_url = (base_url or os.getenv("LLAMA_CPP_URL", _DEFAULT_URL)).rstrip("/")
        self.model = model or os.getenv("LLAMA_CPP_MODEL", "local")
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str], batch_size: int = 20) -> list[list[float]]:
        results: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = httpx.post(
                f"{self.base_url}/v1/embeddings",
                json={"input": batch, "model": self.model},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            # Sort by index to preserve order
            ordered = sorted(data["data"], key=lambda x: x["index"])
            results.extend(item["embedding"] for item in ordered)
        return results

    # ------------------------------------------------------------------
    # Text generation
    # ------------------------------------------------------------------

    def generate(self, prompt: str, **kwargs) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }
        response = httpx.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def grounded_generate(
        self,
        query: str,
        context: list[str],
        top_k: int = 5,
        **kwargs,
    ) -> dict[str, Any]:
        ctx_text = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(context[:top_k]))
        prompt = (
            f"Answer the following question based only on the provided context.\n\n"
            f"Context:\n{ctx_text}\n\n"
            f"Question: {query}\n\n"
            f"Answer:"
        )
        try:
            answer = self.generate(prompt, **kwargs)
            citations = [f"[{i+1}]" for i in range(min(top_k, len(context)))]
            return {
                "answer": answer,
                "citations": citations,
                "snippets": context[:top_k],
                "confidence": 0.9,
                "cost_estimate": 0.0,
            }
        except Exception as e:
            logger.error(f"LlamaCpp grounded_generate failed: {e}")
            return {
                "answer": f"Error: {e}",
                "citations": [],
                "confidence": 0.0,
                "cost_estimate": 0.0,
            }

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"LlamaCpp health check failed: {e}")
            return False
