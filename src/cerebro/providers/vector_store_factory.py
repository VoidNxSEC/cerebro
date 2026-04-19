"""
Factory helpers for vector store providers.
"""

from __future__ import annotations

from cerebro.interfaces.vector_store import VectorStoreProvider
from cerebro.settings import get_settings

VECTOR_STORE_PROVIDER_ALIASES: dict[str, str] = {
    "chroma": "chroma",
    "chromadb": "chroma",
    "local": "chroma",
    "local-chroma": "chroma",
    "pgvector": "pgvector",
    "postgres": "pgvector",
    "postgresql": "pgvector",
    "azure_search": "azure_search",
    "azure-search": "azure_search",
    "azuresearch": "azure_search",
    "cognitive-search": "azure_search",
    "azure-cognitive-search": "azure_search",
    "qdrant": "qdrant",
}


def supported_vector_store_aliases() -> dict[str, str]:
    """Return a copy of supported vector store aliases."""

    return dict(VECTOR_STORE_PROVIDER_ALIASES)


def resolve_vector_store_provider_alias(provider_name: str) -> str:
    """Resolve a vector store alias to its canonical provider name."""

    normalized_name = provider_name.strip().lower()
    resolved = VECTOR_STORE_PROVIDER_ALIASES.get(normalized_name)
    if resolved:
        return resolved

    supported = ", ".join(
        f"{alias}->{canonical}"
        for alias, canonical in sorted(VECTOR_STORE_PROVIDER_ALIASES.items())
    )
    raise ValueError(
        f"Unsupported vector store provider value: {provider_name!r}. "
        f"Supported aliases: {supported}."
    )


def build_vector_store_provider(
    provider_name: str | None = None,
    *,
    persist_directory: str | None = None,
    collection_name: str | None = None,
    namespace: str | None = None,
    url: str | None = None,
    schema: str | None = None,
    embedding_dimensions: int | None = None,
    index_type: str | None = None,
    # Azure AI Search specific
    azure_search_endpoint: str | None = None,
    azure_search_index_name: str | None = None,
    azure_search_api_key: str | None = None,
    # Qdrant specific
    qdrant_api_key: str | None = None,
) -> VectorStoreProvider:
    """Build the configured vector store provider."""

    settings = get_settings()
    canonical_name = resolve_vector_store_provider_alias(
        provider_name or settings.vector_store_provider,
    )

    if canonical_name == "chroma":
        from cerebro.providers.chroma import ChromaVectorStoreProvider

        return ChromaVectorStoreProvider(
            persist_directory=persist_directory or settings.vector_store_persist_directory,
            collection_name=collection_name or settings.vector_store_collection_name,
            default_namespace=namespace or settings.vector_store_namespace,
        )

    if canonical_name == "pgvector":
        from cerebro.providers.pgvector import PgVectorStoreProvider

        return PgVectorStoreProvider(
            dsn=url or settings.vector_store_url,
            collection_name=collection_name or settings.vector_store_collection_name,
            default_namespace=namespace or settings.vector_store_namespace,
            schema=schema or settings.vector_store_schema,
            embedding_dimensions=(
                embedding_dimensions
                if embedding_dimensions is not None
                else settings.vector_store_embedding_dimensions
            ),
            index_type=index_type or settings.vector_store_index_type,
        )

    if canonical_name == "azure_search":
        from cerebro.providers.azure_search import AzureSearchVectorStoreProvider

        return AzureSearchVectorStoreProvider(
            service_endpoint=azure_search_endpoint or settings.azure_search_endpoint,
            index_name=azure_search_index_name or settings.azure_search_index_name,
            api_key=azure_search_api_key or settings.azure_search_api_key,
            default_namespace=namespace or settings.vector_store_namespace,
            embedding_dimensions=(
                embedding_dimensions
                if embedding_dimensions is not None
                else settings.vector_store_embedding_dimensions
            ),
        )

    if canonical_name == "qdrant":
        from cerebro.providers.qdrant import QdrantVectorStoreProvider

        return QdrantVectorStoreProvider(
            url=url or settings.qdrant_url,
            api_key=qdrant_api_key or settings.qdrant_api_key,
            collection_name=collection_name or settings.vector_store_collection_name,
            default_namespace=namespace or settings.vector_store_namespace,
            embedding_dimensions=(
                embedding_dimensions
                if embedding_dimensions is not None
                else settings.vector_store_embedding_dimensions
            ),
        )

    raise ValueError(
        f"Vector store provider is not implemented yet: {canonical_name!r}."
    )
