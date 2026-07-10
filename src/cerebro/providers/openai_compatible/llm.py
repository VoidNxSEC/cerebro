"""
OpenAI-compatible LLM Provider

Implements the LLMProvider interface using OpenAI-style HTTP endpoints.
This adapter is intentionally generic so it can target OpenAI-compatible
servers such as local inference gateways, vLLM, LM Studio, or managed APIs.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

from cerebro.interfaces.llm import LLMProvider

logger = logging.getLogger("cerebro.providers.openai_compatible")

_DEFAULT_URL = "http://localhost:8000"
_DEFAULT_MODEL = "current-model"
_DEFAULT_TIMEOUT = 120.0


def _build_headers(api_key: str | None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _request_json(
    url: str,
    payload: dict[str, Any] | None,
    timeout: float,
    api_key: str | None = None,
    method: str = "POST",
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers=_build_headers(api_key),
        method=method,
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _request_status(url: str, timeout: float, api_key: str | None = None) -> int:
    req = urllib.request.Request(url, method="GET", headers=_build_headers(api_key))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


class OpenAICompatibleProvider(LLMProvider):
    """LLM provider backed by an OpenAI-compatible HTTP API."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ):
        self.base_url = (base_url or os.getenv("OPENAI_COMPATIBLE_URL", _DEFAULT_URL)).rstrip("/")
        self.model = model or os.getenv("OPENAI_COMPATIBLE_MODEL", _DEFAULT_MODEL)
        self.api_key = api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY")
        self.timeout = timeout or float(os.getenv("OPENAI_COMPATIBLE_TIMEOUT", str(_DEFAULT_TIMEOUT)))

    def embed(self, text: str) -> list[float]:
        embeddings = self.embed_batch([text], batch_size=1)
        return embeddings[0] if embeddings else []

    def embed_batch(self, texts: list[str], batch_size: int = 20) -> list[list[float]]:
        results: list[list[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            data = _request_json(
                f"{self.base_url}/v1/embeddings",
                {"input": batch, "model": self.model},
                self.timeout,
                api_key=self.api_key,
            )
            ordered = sorted(data.get("data", []), key=lambda item: item["index"])
            results.extend(item["embedding"] for item in ordered)

        return results

    def generate(self, prompt: str, **kwargs) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        if "stop" in kwargs:
            payload["stop"] = kwargs["stop"]

        data = _request_json(
            f"{self.base_url}/v1/chat/completions",
            payload,
            self.timeout,
            api_key=self.api_key,
        )
        return data["choices"][0]["message"]["content"]

    def grounded_generate(
        self,
        query: str,
        context: list[str],
        top_k: int = 5,
        **kwargs,
    ) -> dict[str, Any]:
        ctx_text = "\n\n".join(f"[{i + 1}] {item}" for i, item in enumerate(context[:top_k]))
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
        except Exception as exc:
            logger.error("OpenAI-compatible grounded_generate failed: %s", exc)
            return {
                "answer": f"Error: {exc}",
                "citations": [],
                "snippets": [],
                "confidence": 0.0,
                "cost_estimate": 0.0,
            }

    def health_check(self) -> bool:
        try:
            status = _request_status(f"{self.base_url}/health", self.timeout, api_key=self.api_key)
            if status == 200:
                return True

            status = _request_status(f"{self.base_url}/v1/models", self.timeout, api_key=self.api_key)
            return status == 200
        except Exception as exc:
            logger.warning("OpenAI-compatible health check failed: %s", exc)
            return False


OpenAICompatibleLLMProvider = OpenAICompatibleProvider
