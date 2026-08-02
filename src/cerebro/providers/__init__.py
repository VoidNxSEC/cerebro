"""
Cerebro providers module.

Concrete implementations of the provider interfaces used by the local-first
core and optional cloud integrations.
"""

from .vector_store_factory import (
    build_vector_store_provider,
    resolve_vector_store_provider_alias,
    supported_vector_store_aliases,
)
from .pgvector import PgVectorStoreProvider

__all__ = [
    "PgVectorStoreProvider",
    "build_vector_store_provider",
    "resolve_vector_store_provider_alias",
    "supported_vector_store_aliases",
]
