"""
Phantom Interfaces Module

Defines abstract base classes for pluggable providers:
- LLMProvider: Interface for Language Model providers
- VectorStoreProvider: Interface for Vector Store providers
"""

from .llm import LLMProvider
from .vector_store import VectorStoreProvider

__all__ = ["LLMProvider", "VectorStoreProvider"]
