"""
Cerebro Interfaces Module

Defines abstract base classes for pluggable providers:
- LLMProvider: Interface for Language Model providers
- VectorStoreProvider: Interface for Vector Store providers
"""

from .llm import LLMProvider
from .vector_store import (
    MetadataFilters,
    MetadataScalar,
    StoredVectorDocument,
    VectorSearchResult,
    VectorStoreHealth,
    VectorStoreProvider,
)

__all__ = [
    "LLMProvider",
    "MetadataFilters",
    "MetadataScalar",
    "StoredVectorDocument",
    "VectorSearchResult",
    "VectorStoreHealth",
    "VectorStoreProvider",
]
