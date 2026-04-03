"""
OpenAI-compatible LLM provider.

Generic stdlib-only adapter for OpenAI-style chat and embedding endpoints.
"""

from .llm import OpenAICompatibleLLMProvider, OpenAICompatibleProvider

__all__ = ["OpenAICompatibleProvider", "OpenAICompatibleLLMProvider"]
