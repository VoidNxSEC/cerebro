"""Tests for vector store settings and factory resolution."""

from unittest.mock import patch

import pytest

from cerebro.providers.vector_store_factory import (
    build_vector_store_provider,
    resolve_vector_store_provider_alias,
    supported_vector_store_aliases,
)
from cerebro.settings import reset_settings_cache


def test_supported_vector_store_aliases_include_core_backends():
    aliases = supported_vector_store_aliases()
    assert aliases["chroma"] == "chroma"
    assert aliases["chromadb"] == "chroma"
    assert aliases["pgvector"] == "pgvector"
    assert aliases["postgresql"] == "pgvector"


def test_resolve_vector_store_provider_alias_rejects_unknown():
    with pytest.raises(ValueError, match="Supported aliases"):
        resolve_vector_store_provider_alias("not-a-provider")


def test_build_vector_store_provider_uses_settings(monkeypatch):
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_PROVIDER", "chromadb")
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_COLLECTION_NAME", "custom_collection")
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_NAMESPACE", "prod")
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_PERSIST_DIRECTORY", "./custom_db")
    reset_settings_cache()

    with patch(
        "cerebro.providers.chroma.ChromaVectorStoreProvider",
    ) as mock_provider:
        build_vector_store_provider()

    mock_provider.assert_called_once_with(
        persist_directory="./custom_db",
        collection_name="custom_collection",
        default_namespace="prod",
    )


def test_build_vector_store_provider_explicit_arguments_override_settings(monkeypatch):
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_PROVIDER", "chroma")
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_COLLECTION_NAME", "env_collection")
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_NAMESPACE", "env_namespace")
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_PERSIST_DIRECTORY", "./env_db")
    reset_settings_cache()

    with patch(
        "cerebro.providers.chroma.ChromaVectorStoreProvider",
    ) as mock_provider:
        build_vector_store_provider(
            persist_directory="./override_db",
            collection_name="override_collection",
            namespace="staging",
        )

    mock_provider.assert_called_once_with(
        persist_directory="./override_db",
        collection_name="override_collection",
        default_namespace="staging",
    )


def test_build_pgvector_store_provider_uses_settings(monkeypatch):
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_PROVIDER", "postgresql")
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_URL", "postgresql://cerebro:test@localhost:5432/cerebro")
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_COLLECTION_NAME", "prod_documents")
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_NAMESPACE", "prod")
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_SCHEMA", "rag")
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_EMBEDDING_DIMENSIONS", "768")
    monkeypatch.setenv("CEREBRO_VECTOR_STORE_INDEX_TYPE", "ivfflat")
    reset_settings_cache()

    with patch(
        "cerebro.providers.pgvector.PgVectorStoreProvider",
    ) as mock_provider:
        build_vector_store_provider()

    mock_provider.assert_called_once_with(
        dsn="postgresql://cerebro:test@localhost:5432/cerebro",
        collection_name="prod_documents",
        default_namespace="prod",
        schema="rag",
        embedding_dimensions=768,
        index_type="ivfflat",
    )
