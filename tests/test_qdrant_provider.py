"""Tests for the Qdrant-backed vector store provider.

Fully mocked — no live Qdrant server required. Uses sys.modules stubs so the
suite runs even when the optional `qdrant-client` dependency is not installed.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock

# -----------------------------------------------------------------------------
# sys.modules stubs — installed before the provider is imported so the method-
# level `from qdrant_client.http.models import ...` imports resolve to our fakes.
# -----------------------------------------------------------------------------


@dataclass
class _FakeMatchValue:
    value: Any


@dataclass
class _FakeFieldCondition:
    key: str
    match: _FakeMatchValue


@dataclass
class _FakeFilter:
    must: list = field(default_factory=list)


@dataclass
class _FakePointStruct:
    id: str
    vector: list[float]
    payload: dict[str, Any]


@dataclass
class _FakePointIdsList:
    points: list[str]


@dataclass
class _FakeVectorParams:
    size: int
    distance: str


class _FakeDistance:
    COSINE = "COSINE"


_models_stub = MagicMock()
_models_stub.MatchValue = _FakeMatchValue
_models_stub.FieldCondition = _FakeFieldCondition
_models_stub.Filter = _FakeFilter
_models_stub.PointStruct = _FakePointStruct
_models_stub.PointIdsList = _FakePointIdsList
_models_stub.VectorParams = _FakeVectorParams
_models_stub.Distance = _FakeDistance

_http_stub = MagicMock()
_http_stub.models = _models_stub

_qdrant_client_stub = MagicMock()
_qdrant_client_stub.http = _http_stub
_qdrant_client_stub.QdrantClient = MagicMock

_QDRANT_STUBS = {
    "qdrant_client": _qdrant_client_stub,
    "qdrant_client.http": _http_stub,
    "qdrant_client.http.models": _models_stub,
}
for _mod, _stub in _QDRANT_STUBS.items():
    sys.modules.setdefault(_mod, _stub)


from cerebro.providers.qdrant import QdrantVectorStoreProvider  # noqa: E402
from cerebro.providers.vector_store_factory import (  # noqa: E402
    resolve_vector_store_provider_alias,
    supported_vector_store_aliases,
)


# -----------------------------------------------------------------------------
# Fake Qdrant client — captures calls and returns configured hits.
# -----------------------------------------------------------------------------


class _FakeScored:
    def __init__(self, id: str, score: float, payload: dict[str, Any]):
        self.id = id
        self.score = score
        self.payload = payload


class _FakeRecord:
    def __init__(self, id: str, payload: dict[str, Any], vector: list[float] | None):
        self.id = id
        self.payload = payload
        self.vector = vector


class _FakeCountResult:
    def __init__(self, count: int):
        self.count = count


class _FakeCollectionInfo:
    def __init__(self, points_count: int = 0):
        self.points_count = points_count


class _FakeQdrantClient:
    """Captures every call; configurable search/scroll results."""

    def __init__(
        self,
        *,
        search_hits: list[_FakeScored] | None = None,
        scroll_records: list[_FakeRecord] | None = None,
        exists: bool = False,
        count_value: int = 0,
    ):
        self.search_hits = search_hits or []
        self.scroll_records = scroll_records or []
        self.exists = exists
        self._count_value = count_value
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get_collection(self, collection_name: str):
        self.calls.append(("get_collection", {"collection_name": collection_name}))
        if not self.exists:
            raise RuntimeError("collection does not exist")
        return _FakeCollectionInfo(points_count=0)

    def create_collection(self, **kwargs):
        self.calls.append(("create_collection", kwargs))
        self.exists = True

    def upsert(self, **kwargs):
        self.calls.append(("upsert", kwargs))

    def search(self, **kwargs):
        self.calls.append(("search", kwargs))
        return self.search_hits

    def delete(self, **kwargs):
        self.calls.append(("delete", kwargs))

    def delete_collection(self, collection_name: str):
        self.calls.append(("delete_collection", {"collection_name": collection_name}))
        self.exists = False

    def count(self, **kwargs):
        self.calls.append(("count", kwargs))
        return _FakeCountResult(self._count_value)

    def scroll(self, **kwargs):
        self.calls.append(("scroll", kwargs))
        return self.scroll_records, None


def _make_provider(client: _FakeQdrantClient, **overrides) -> QdrantVectorStoreProvider:
    params = dict(
        url="http://localhost:6333",
        collection_name="docs",
        default_namespace="prod",
        embedding_dimensions=4,
    )
    params.update(overrides)
    provider = QdrantVectorStoreProvider(**params)
    provider._client = lambda: client  # type: ignore[method-assign]
    return provider


# -----------------------------------------------------------------------------
# Factory / alias resolution
# -----------------------------------------------------------------------------


def test_qdrant_factory_alias_resolves():
    assert resolve_vector_store_provider_alias("qdrant") == "qdrant"
    assert "qdrant" in supported_vector_store_aliases()


# -----------------------------------------------------------------------------
# Schema bootstrap
# -----------------------------------------------------------------------------


def test_initialize_schema_creates_collection_when_missing():
    client = _FakeQdrantClient(exists=False)
    provider = _make_provider(client)

    result = provider.initialize_schema()

    assert result["backend"] == "qdrant"
    assert result["initialized"] is True
    kinds = [name for name, _ in client.calls]
    assert "get_collection" in kinds
    assert "create_collection" in kinds
    create_kwargs = next(kw for name, kw in client.calls if name == "create_collection")
    assert create_kwargs["collection_name"] == "docs"
    assert create_kwargs["vectors_config"].size == 4
    assert create_kwargs["vectors_config"].distance == _FakeDistance.COSINE


def test_initialize_schema_is_idempotent_when_collection_exists():
    client = _FakeQdrantClient(exists=True)
    provider = _make_provider(client)

    provider.initialize_schema()

    kinds = [name for name, _ in client.calls]
    assert "get_collection" in kinds
    assert "create_collection" not in kinds


# -----------------------------------------------------------------------------
# Upsert
# -----------------------------------------------------------------------------


def test_upsert_documents_builds_points_and_preserves_original_id():
    client = _FakeQdrantClient()
    provider = _make_provider(client)

    inserted = provider.upsert_documents(
        [
            {
                "id": "intel-1",
                "content": "def hello(): pass",
                "title": "Hello",
                "source": "repo/main.py",
            }
        ],
        [[0.1, 0.2, 0.3, 0.4]],
    )

    assert inserted == 1
    name, kwargs = client.calls[-1]
    assert name == "upsert"
    assert kwargs["collection_name"] == "docs"
    point = kwargs["points"][0]
    assert point.vector == [0.1, 0.2, 0.3, 0.4]
    assert point.payload["_cerebro_id"] == "intel-1"
    assert point.payload["namespace"] == "prod"
    assert point.payload["title"] == "Hello"


def test_upsert_documents_rejects_length_mismatch():
    provider = _make_provider(_FakeQdrantClient())

    try:
        provider.upsert_documents(
            [{"id": "a", "content": "x"}],
            [[0.1], [0.2]],
        )
    except ValueError as exc:
        assert "count" in str(exc)
    else:
        raise AssertionError("expected ValueError on length mismatch")


def test_upsert_documents_empty_is_noop():
    client = _FakeQdrantClient()
    provider = _make_provider(client)

    assert provider.upsert_documents([], []) == 0
    assert client.calls == []


# -----------------------------------------------------------------------------
# Search
# -----------------------------------------------------------------------------


def test_search_applies_namespace_and_filters():
    client = _FakeQdrantClient(
        search_hits=[
            _FakeScored(
                id="point-uuid",
                score=0.87,
                payload={
                    "_cerebro_id": "intel-1",
                    "content": "def hello(): pass",
                    "title": "Hello",
                    "source": "repo/main.py",
                    "namespace": "prod",
                    "type": "techint",
                },
            )
        ]
    )
    provider = _make_provider(client)

    results = provider.search(
        [0.25, 0.75, 0.5, 0.1],
        top_k=3,
        filters={"type": "techint"},
        namespace="prod",
    )

    assert len(results) == 1
    hit = results[0]
    assert hit.id == "intel-1"
    assert hit.source == "repo/main.py"
    assert hit.title == "Hello"
    assert hit.score == 0.87

    name, kwargs = client.calls[-1]
    assert name == "search"
    assert kwargs["limit"] == 3
    f = kwargs["query_filter"]
    keys = sorted(cond.key for cond in f.must)
    assert keys == ["namespace", "type"]


def test_search_returns_empty_when_top_k_zero():
    client = _FakeQdrantClient()
    provider = _make_provider(client)

    assert provider.search([0.1, 0.2, 0.3, 0.4], top_k=0) == []
    assert client.calls == []


# -----------------------------------------------------------------------------
# Delete / clear
# -----------------------------------------------------------------------------


def test_delete_documents_maps_ids_to_uuid5():
    client = _FakeQdrantClient()
    provider = _make_provider(client)

    deleted = provider.delete_documents(["intel-1", "intel-2"])

    assert deleted == 2
    name, kwargs = client.calls[-1]
    assert name == "delete"
    selector = kwargs["points_selector"]
    assert len(selector.points) == 2
    # UUID5 deterministic — same ID always resolves to same UUID
    assert selector.points[0] != "intel-1"  # it's a UUID, not the original string


def test_clear_namespace_uses_filter_selector():
    client = _FakeQdrantClient()
    provider = _make_provider(client)

    provider.clear(namespace="prod")

    name, kwargs = client.calls[-1]
    assert name == "delete"
    selector = kwargs["points_selector"]
    assert isinstance(selector, _FakeFilter)
    assert selector.must[0].key == "namespace"
    assert selector.must[0].match.value == "prod"


def test_clear_without_namespace_recreates_collection():
    client = _FakeQdrantClient(exists=True)
    provider = _make_provider(client, default_namespace=None)

    provider.clear()

    names = [n for n, _ in client.calls]
    assert "delete_collection" in names


# -----------------------------------------------------------------------------
# Count / health
# -----------------------------------------------------------------------------


def test_document_count_scopes_to_namespace():
    client = _FakeQdrantClient(count_value=42)
    provider = _make_provider(client)

    assert provider.get_document_count(namespace="prod") == 42
    name, kwargs = client.calls[-1]
    assert name == "count"
    assert kwargs["exact"] is True
    assert kwargs["count_filter"].must[0].key == "namespace"


def test_health_check_true_when_get_collection_succeeds():
    client = _FakeQdrantClient(exists=True)
    provider = _make_provider(client)
    assert provider.health_check() is True


def test_health_check_false_when_server_unreachable():
    class _Broken:
        def get_collection(self, *args, **kwargs):
            raise RuntimeError("boom")

    provider = QdrantVectorStoreProvider(
        url="http://localhost:6333",
        collection_name="docs",
        embedding_dimensions=4,
    )
    provider._client = lambda: _Broken()  # type: ignore[method-assign]

    assert provider.health_check() is False


def test_backend_info_advertises_capabilities():
    provider = _make_provider(_FakeQdrantClient())

    info = provider.get_backend_info()

    assert info["backend"] == "qdrant"
    assert info["supports_filters"] is True
    assert info["supports_namespace"] is True
    assert info["embedding_dimensions"] == 4


# -----------------------------------------------------------------------------
# Export (migration)
# -----------------------------------------------------------------------------


def test_export_documents_returns_stored_vectors():
    client = _FakeQdrantClient(
        scroll_records=[
            _FakeRecord(
                id="point-uuid",
                payload={
                    "_cerebro_id": "intel-1",
                    "content": "x",
                    "namespace": "prod",
                    "title": "T",
                    "source": "s.py",
                },
                vector=[0.1, 0.2, 0.3, 0.4],
            )
        ]
    )
    provider = _make_provider(client)

    exported = provider.export_documents(namespace="prod", limit=10, offset=5)

    assert len(exported) == 1
    doc = exported[0]
    assert doc.id == "intel-1"
    assert doc.embedding == [0.1, 0.2, 0.3, 0.4]
    assert doc.namespace == "prod"
    assert doc.title == "T"
    assert doc.source == "s.py"


def test_canonical_metadata_round_trips_through_upsert():
    """Smoke test: canonical fields set by build_canonical_fields survive upsert payload."""
    client = _FakeQdrantClient()
    provider = _make_provider(client)

    provider.upsert_documents(
        [
            {
                "id": "intel-1",
                "content": "x",
                "content_hash": "abc123",
                "ingested_at": "2026-04-24T00:00:00Z",
                "chunk_id": "repo:src:1",
                "_cerebro_schema_version": "1",
            }
        ],
        [[0.1, 0.2, 0.3, 0.4]],
    )

    point = client.calls[-1][1]["points"][0]
    assert point.payload["content_hash"] == "abc123"
    assert point.payload["ingested_at"] == "2026-04-24T00:00:00Z"
    assert point.payload["chunk_id"] == "repo:src:1"
    assert point.payload["_cerebro_schema_version"] == "1"
