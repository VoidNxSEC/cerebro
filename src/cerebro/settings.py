"""
Central settings for Cerebro.

Settings are intentionally lightweight and environment-driven so core runtime
paths can be shared by CLI, API, tests, and future service entrypoints.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True, slots=True)
class CerebroSettings:
    """Environment-backed runtime settings."""

    vector_store_provider: str = "chroma"
    vector_store_url: str | None = None
    vector_store_namespace: str | None = None
    vector_store_schema: str = "public"
    vector_store_collection_name: str = "cerebro_documents"
    vector_store_persist_directory: str = "./data/vector_db"
    vector_store_embedding_dimensions: int | None = None
    vector_store_index_type: str = "hnsw"

    # Azure AI Search
    azure_search_endpoint: str | None = None
    azure_search_index_name: str | None = None
    azure_search_api_key: str | None = None

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    # LLM provider
    llm_provider: str = "llamacpp"

    @classmethod
    def from_env(cls) -> CerebroSettings:
        return cls(
            vector_store_provider=os.getenv("CEREBRO_VECTOR_STORE_PROVIDER", "chroma")
            .strip()
            .lower(),
            vector_store_url=os.getenv("CEREBRO_VECTOR_STORE_URL"),
            vector_store_namespace=os.getenv("CEREBRO_VECTOR_STORE_NAMESPACE"),
            vector_store_schema=os.getenv("CEREBRO_VECTOR_STORE_SCHEMA", "public").strip(),
            vector_store_collection_name=os.getenv(
                "CEREBRO_VECTOR_STORE_COLLECTION_NAME",
                "cerebro_documents",
            )
            .strip(),
            vector_store_persist_directory=os.getenv(
                "CEREBRO_VECTOR_STORE_PERSIST_DIRECTORY",
                "./data/vector_db",
            )
            .strip(),
            vector_store_embedding_dimensions=(
                int(raw_dimensions)
                if (raw_dimensions := os.getenv("CEREBRO_VECTOR_STORE_EMBEDDING_DIMENSIONS"))
                else None
            ),
            vector_store_index_type=os.getenv(
                "CEREBRO_VECTOR_STORE_INDEX_TYPE",
                "hnsw",
            )
            .strip()
            .lower(),
            azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            azure_search_index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            azure_search_api_key=os.getenv("AZURE_SEARCH_API_KEY"),
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333").strip(),
            qdrant_api_key=os.getenv("QDRANT_API_KEY"),
            llm_provider=os.getenv("CEREBRO_LLM_PROVIDER", "llamacpp").strip().lower(),
        )


@lru_cache(maxsize=1)
def get_settings() -> CerebroSettings:
    """Return cached runtime settings."""

    return CerebroSettings.from_env()


def reset_settings_cache() -> None:
    """Clear the cached settings snapshot. Useful in tests."""

    get_settings.cache_clear()
