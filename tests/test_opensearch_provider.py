"""Tests for the OpenSearch-backed vector store provider.

Fully mocked — no live OpenSearch cluster required. Uses sys.modules stubs so
the suite runs even without the optional `opensearch-py` dependency.
"""

from __future__ import annotations

import json
import sys
from typing import Any
from unittest.mock import MagicMock

# -----------------------------------------------------------------------------
# sys.modules stubs for opensearchpy (imported lazily inside `_client()`).
# -----------------------------------------------------------------------------

_opensearchpy_stub = MagicMock()
_opensearchpy_stub.OpenSearch = MagicMock
_opensearchpy_stub.RequestsHttpConnection = MagicMock

sys.modules.setdefault("opensearchpy", _opensearchpy_stub)


from cerebro.providers.opensearch import OpenSearchVectorStoreProvider  # noqa: E402
from cerebro.providers.vector_store_factory import (  # noqa: E402
    resolve_vector_store_provider_alias,
    supported_vector_store_aliases,
)


# -----------------------------------------------------------------------------
# Fake OpenSearch client
# -----------------------------------------------------------------------------


class _FakeIndices:
    def __init__(self, *, existing: bool = False):
        self.existing = existing
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def exists(self, *, index: str) -> bool:
        self.calls.append(("exists", {"index": index}))
        return self.existing

    def create(self, *, index: str, body: dict[str, Any]) -> None:
        self.calls.append(("create", {"index": index, "body": body}))
        self.existing = True

    def delete(self, *, index: str) -> None:
        self.calls.append(("delete", {"index": index}))
        self.existing = False


class _FakeCluster:
    def __init__(self, *, healthy: bool = True):
        self.healthy = healthy
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def health(self, *, index: str):
        self.calls.append(("health", {"index": index}))
        if not self.healthy:
            raise RuntimeError("cluster unhealthy")
        return {"status": "green"}


class _FakeOpenSearch:
    def __init__(
        self,
        *,
        search_response: dict[str, Any] | None = None,
        bulk_response: dict[str, Any] | None = None,
        count_response: dict[str, Any] | None = None,
        indices_existing: bool = False,
        cluster_healthy: bool = True,
    ):
        self.indices = _FakeIndices(existing=indices_existing)
        self.cluster = _FakeCluster(healthy=cluster_healthy)
        self.search_response = search_response or {"hits": {"hits": []}}
        self.bulk_response = bulk_response or {"items": []}
        self.count_response = count_response or {"count": 0}
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def search(self, **kwargs):
        self.calls.append(("search", kwargs))
        return self.search_response

    def bulk(self, **kwargs):
        self.calls.append(("bulk", kwargs))
        return self.bulk_response

    def count(self, **kwargs):
        self.calls.append(("count", kwargs))
        return self.count_response

    def delete_by_query(self, **kwargs):
        self.calls.append(("delete_by_query", kwargs))


def _make_provider(client: _FakeOpenSearch, **overrides) -> OpenSearchVectorStoreProvider:
    params = dict(
        url="http://localhost:9200",
        index_name="cerebro-test",
        default_namespace="prod",
        embedding_dimensions=4,
    )
    params.update(overrides)
    provider = OpenSearchVectorStoreProvider(**params)
    provider._client = lambda: client  # type: ignore[method-assign]
    return provider


# -----------------------------------------------------------------------------
# Factory / alias resolution
# -----------------------------------------------------------------------------


def test_opensearch_factory_alias_resolves():
    assert resolve_vector_store_provider_alias("opensearch") == "opensearch"
    assert resolve_vector_store_provider_alias("elasticsearch") == "opensearch"
    assert resolve_vector_store_provider_alias("elastic") == "opensearch"
    assert "opensearch" in supported_vector_store_aliases()


# -----------------------------------------------------------------------------
# Schema bootstrap
# -----------------------------------------------------------------------------


def test_initialize_schema_creates_index_with_knn_vector():
    client = _FakeOpenSearch(indices_existing=False)
    provider = _make_provider(client)

    result = provider.initialize_schema()

    assert result["initialized"] is True
    create_call = next(call for call in client.indices.calls if call[0] == "create")
    mapping = create_call[1]["body"]
    vector_prop = mapping["mappings"]["properties"]["content_vector"]
    assert vector_prop["type"] == "knn_vector"
    assert vector_prop["dimension"] == 4
    assert vector_prop["method"]["space_type"] == "cosinesimil"
    assert mapping["settings"]["index"]["knn"] is True


def test_initialize_schema_es_compat_uses_dense_vector():
    client = _FakeOpenSearch(indices_existing=False)
    provider = _make_provider(client, es_compat=True)

    provider.initialize_schema()

    create_call = next(call for call in client.indices.calls if call[0] == "create")
    mapping = create_call[1]["body"]
    vector_prop = mapping["mappings"]["properties"]["content_vector"]
    assert vector_prop["type"] == "dense_vector"
    assert vector_prop["dims"] == 4
    assert vector_prop["similarity"] == "cosine"


def test_initialize_schema_is_idempotent():
    client = _FakeOpenSearch(indices_existing=True)
    provider = _make_provider(client)

    result = provider.initialize_schema()

    assert result["initialized"] is False
    assert result["already_existed"] is True
    create_calls = [c for c in client.indices.calls if c[0] == "create"]
    assert create_calls == []


# -----------------------------------------------------------------------------
# Upsert
# -----------------------------------------------------------------------------


def test_upsert_documents_issues_bulk_index_actions():
    client = _FakeOpenSearch(bulk_response={"items": []})
    provider = _make_provider(client)

    inserted = provider.upsert_documents(
        [
            {
                "id": "intel-1",
                "content": "def hello(): pass",
                "title": "Hello",
                "source": "repo/main.py",
                "type": "techint",
            }
        ],
        [[0.1, 0.2, 0.3, 0.4]],
    )

    assert inserted == 1
    name, kwargs = client.calls[-1]
    assert name == "bulk"
    lines = kwargs["body"].strip().split("\n")
    assert len(lines) == 2
    action = json.loads(lines[0])
    assert action["index"]["_index"] == "cerebro-test"
    assert action["index"]["_id"] == "intel-1"
    body = json.loads(lines[1])
    assert body["content"] == "def hello(): pass"
    assert body["content_vector"] == [0.1, 0.2, 0.3, 0.4]
    assert body["namespace"] == "prod"
    assert body["title"] == "Hello"
    # Non-keyword metadata packed into metadata_json
    metadata = json.loads(body["metadata_json"])
    assert metadata["type"] == "techint"


def test_upsert_documents_empty_is_noop():
    client = _FakeOpenSearch()
    provider = _make_provider(client)

    assert provider.upsert_documents([], []) == 0
    assert client.calls == []


def test_upsert_documents_rejects_length_mismatch():
    provider = _make_provider(_FakeOpenSearch())

    try:
        provider.upsert_documents(
            [{"id": "a", "content": "x"}],
            [[0.1], [0.2]],
        )
    except ValueError as exc:
        assert "count" in str(exc)
    else:
        raise AssertionError("expected ValueError on length mismatch")


def test_upsert_documents_reports_partial_failure():
    client = _FakeOpenSearch(
        bulk_response={
            "items": [
                {"index": {"status": 201}},
                {"index": {"error": {"type": "mapper_parsing_exception"}}},
            ]
        }
    )
    provider = _make_provider(client)

    inserted = provider.upsert_documents(
        [
            {"id": "ok", "content": "a"},
            {"id": "bad", "content": "b"},
        ],
        [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]],
    )
    assert inserted == 1


# -----------------------------------------------------------------------------
# Search
# -----------------------------------------------------------------------------


def test_search_normalises_cosinesimil_score_to_unit_interval():
    client = _FakeOpenSearch(
        search_response={
            "hits": {
                "hits": [
                    {
                        "_id": "intel-1",
                        "_score": 1.9,  # raw cosinesimil in [0,2]
                        "_source": {
                            "content": "def hello(): pass",
                            "namespace": "prod",
                            "title": "Hello",
                            "source": "repo/main.py",
                            "metadata_json": json.dumps({"type": "techint"}),
                        },
                    }
                ]
            }
        }
    )
    provider = _make_provider(client)

    results = provider.search([0.1, 0.2, 0.3, 0.4], top_k=3)

    assert len(results) == 1
    assert round(results[0].score, 3) == 0.95  # 1.9 / 2
    assert results[0].id == "intel-1"
    assert results[0].metadata["type"] == "techint"


def test_search_applies_namespace_and_keyword_filters():
    client = _FakeOpenSearch()
    provider = _make_provider(client)

    provider.search(
        [0.1, 0.2, 0.3, 0.4],
        top_k=5,
        filters={"repo": "my-service", "type": "techint"},
        namespace="prod",
    )

    _, kwargs = client.calls[-1]
    bool_filter = kwargs["body"]["query"]["bool"]["filter"]
    terms = sorted(list(clause["term"].keys())[0] for clause in bool_filter)
    # `type` is not a keyword field → skipped; `repo` is → kept.
    assert "namespace" in terms
    assert "repo" in terms
    assert "type" not in terms


def test_search_hybrid_query_includes_match_clause():
    client = _FakeOpenSearch()
    provider = _make_provider(client, enable_hybrid_search=True)

    provider.search(
        [0.1, 0.2, 0.3, 0.4],
        top_k=5,
        query_text="hello world",
    )

    _, kwargs = client.calls[-1]
    must_clauses = kwargs["body"]["query"]["bool"]["must"]
    match_clauses = [c for c in must_clauses if "match" in c]
    assert len(match_clauses) == 1
    assert match_clauses[0]["match"]["content"]["query"] == "hello world"


def test_search_hybrid_disabled_ignores_query_text():
    client = _FakeOpenSearch()
    provider = _make_provider(client, enable_hybrid_search=False)

    provider.search([0.1, 0.2, 0.3, 0.4], top_k=5, query_text="hello world")

    _, kwargs = client.calls[-1]
    query = kwargs["body"]["query"]
    # Pure knn or bool-with-filter but no match clause
    if "bool" in query:
        must = query["bool"]["must"]
        assert all("match" not in c for c in must)
    else:
        assert "knn" in query


def test_search_min_score_is_scaled_to_raw_range():
    client = _FakeOpenSearch()
    provider = _make_provider(client)

    provider.search([0.1, 0.2, 0.3, 0.4], top_k=5, min_score=0.8)

    _, kwargs = client.calls[-1]
    assert kwargs["body"]["min_score"] == 1.6  # 0.8 * 2


def test_search_returns_empty_when_top_k_zero():
    client = _FakeOpenSearch()
    provider = _make_provider(client)

    assert provider.search([0.1, 0.2, 0.3, 0.4], top_k=0) == []
    assert client.calls == []


# -----------------------------------------------------------------------------
# Delete / clear
# -----------------------------------------------------------------------------


def test_delete_documents_issues_bulk_delete():
    client = _FakeOpenSearch(
        bulk_response={
            "items": [
                {"delete": {"result": "deleted"}},
                {"delete": {"result": "not_found"}},
            ]
        }
    )
    provider = _make_provider(client)

    deleted = provider.delete_documents(["a", "b"])
    assert deleted == 1


def test_clear_namespace_uses_delete_by_query():
    client = _FakeOpenSearch()
    provider = _make_provider(client)

    provider.clear(namespace="prod")

    name, kwargs = client.calls[-1]
    assert name == "delete_by_query"
    assert kwargs["body"]["query"]["term"]["namespace"] == "prod"


def test_clear_without_namespace_drops_and_recreates_index():
    client = _FakeOpenSearch(indices_existing=True)
    provider = _make_provider(client, default_namespace=None)

    provider.clear()

    idx_kinds = [name for name, _ in client.indices.calls]
    assert "delete" in idx_kinds
    assert "create" in idx_kinds


# -----------------------------------------------------------------------------
# Count / health
# -----------------------------------------------------------------------------


def test_document_count_scopes_to_namespace():
    client = _FakeOpenSearch(count_response={"count": 42})
    provider = _make_provider(client)

    assert provider.get_document_count(namespace="prod") == 42
    name, kwargs = client.calls[-1]
    assert name == "count"
    assert kwargs["body"]["query"]["term"]["namespace"] == "prod"


def test_health_check_true_when_cluster_healthy():
    client = _FakeOpenSearch(cluster_healthy=True)
    provider = _make_provider(client)
    assert provider.health_check() is True


def test_health_check_false_when_cluster_unreachable():
    client = _FakeOpenSearch(cluster_healthy=False)
    provider = _make_provider(client)
    assert provider.health_check() is False


def test_backend_info_advertises_capabilities():
    provider = _make_provider(_FakeOpenSearch())
    info = provider.get_backend_info()

    assert info["backend"] == "opensearch"
    assert info["supports_filters"] is True
    assert info["supports_namespace"] is True
    assert "namespace" in info["filterable_fields"]
    assert "repo" in info["filterable_fields"]


# -----------------------------------------------------------------------------
# Export
# -----------------------------------------------------------------------------


def test_export_documents_returns_stored_vectors():
    client = _FakeOpenSearch(
        search_response={
            "hits": {
                "hits": [
                    {
                        "_id": "intel-1",
                        "_source": {
                            "content": "x",
                            "content_vector": [0.1, 0.2, 0.3, 0.4],
                            "namespace": "prod",
                            "title": "T",
                            "source": "s.py",
                            "metadata_json": json.dumps({"type": "techint"}),
                        },
                    }
                ]
            }
        }
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
    assert doc.metadata["type"] == "techint"


def test_canonical_metadata_round_trips_through_upsert():
    client = _FakeOpenSearch(bulk_response={"items": []})
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

    _, kwargs = client.calls[-1]
    lines = kwargs["body"].strip().split("\n")
    body = json.loads(lines[1])
    metadata = json.loads(body["metadata_json"])
    assert metadata["content_hash"] == "abc123"
    assert metadata["ingested_at"] == "2026-04-24T00:00:00Z"
    assert metadata["chunk_id"] == "repo:src:1"
    assert metadata["_cerebro_schema_version"] == "1"
