"""
LlamaCpp LLM Provider

Implements LLMProvider interface for a local llama.cpp server.
The server must expose an OpenAI-compatible API (llama-server --port 8081).

Uses only stdlib (urllib) — no extra dependencies required.

Env vars:
  LLAMA_CPP_URL   Base URL of the llama.cpp server (default: http://localhost:8081)
  LLAMA_CPP_MODEL Model name to pass in requests (default: local)
"""

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

from cerebro.interfaces.llm import LLMProvider

logger = logging.getLogger("cerebro.providers.llamacpp")

_DEFAULT_URL = "http://localhost:8081"
_DEFAULT_MODEL = "current-model"


def _post(url: str, payload: dict, timeout: float) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _get(url: str, timeout: float) -> int:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


class LlamaCppProvider(LLMProvider):
    """LLM provider backed by a local llama.cpp server (OpenAI-compatible API)."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ):
        self.base_url = (base_url or os.getenv("LLAMA_CPP_URL", _DEFAULT_URL)).rstrip("/")
        self.model = model or os.getenv("LLAMA_CPP_MODEL", _DEFAULT_MODEL)
        # Allow override via env; default 600s — large local models can be slow
        self.timeout = timeout or float(os.getenv("LLAMA_CPP_TIMEOUT", "600"))

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str], batch_size: int = 20) -> list[list[float]]:
        results: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                data = _post(
                    f"{self.base_url}/v1/embeddings",
                    {"input": batch, "model": self.model},
                    self.timeout,
                )
            except urllib.error.HTTPError as e:
                if e.code == 501:
                    raise RuntimeError(
                        "llama.cpp server does not support embeddings. "
                        "Restart with: llama-server --embeddings --port 8081"
                    ) from e
                raise
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
        data = _post(f"{self.base_url}/v1/chat/completions", payload, self.timeout)
        return data["choices"][0]["message"]["content"]

    def chat(self, messages: list[dict], **kwargs) -> str:
        """Send a multi-turn conversation and return the assistant reply."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        data = _post(f"{self.base_url}/v1/chat/completions", payload, self.timeout)
        return data["choices"][0]["message"]["content"]

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
            return {
                "answer": answer,
                "citations": [f"[{i+1}]" for i in range(min(top_k, len(context)))],
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
            return _get(f"{self.base_url}/health", timeout=5.0) == 200
        except Exception as e:
            logger.warning(f"LlamaCpp health check failed: {e}")
            return False
