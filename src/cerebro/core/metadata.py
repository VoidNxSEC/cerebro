"""
Canonical document metadata schema for Cerebro.

Every document stored in any vector store backend must carry these fields so
ingestion pipelines, retrievers, and migration tools share a stable contract.

Fields
------
content_hash        16-char hex prefix of SHA-256(content). Used to detect
                    unchanged chunks and skip re-embedding.
ingested_at         ISO-8601 UTC timestamp of when the document was ingested.
chunk_id            Stable chunk identifier: "<doc_id>:<chunk_index>" or "<doc_id>"
                    for whole-document ingestion.
backend_namespace   The resolved namespace written to the store.  Empty string
                    means the default (unscoped) namespace.
_cerebro_schema_version
                    Integer string incremented when the canonical schema changes,
                    allowing future migration tooling to detect stale documents.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

CANONICAL_METADATA_VERSION: str = "1"

CANONICAL_FIELDS: frozenset[str] = frozenset(
    {
        "content_hash",
        "ingested_at",
        "chunk_id",
        "backend_namespace",
        "_cerebro_schema_version",
    }
)


def build_canonical_fields(
    content: str,
    doc_id: str,
    namespace: str | None = None,
    chunk_index: int | None = None,
) -> dict[str, Any]:
    """
    Return the canonical metadata fields for a document at ingestion time.

    Args:
        content:      Raw text content of the chunk.
        doc_id:       Stable document identifier (before any backend ID mapping).
        namespace:    Resolved logical namespace, or None for the default scope.
        chunk_index:  Integer position of this chunk within the source document,
                      or None for whole-document ingestion.

    Returns:
        dict with all CANONICAL_FIELDS populated.
    """
    content_hash = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()[:16]
    chunk_id = f"{doc_id}:{chunk_index}" if chunk_index is not None else doc_id

    return {
        "content_hash": content_hash,
        "ingested_at": datetime.now(UTC).isoformat(),
        "chunk_id": chunk_id,
        "backend_namespace": namespace or "",
        "_cerebro_schema_version": CANONICAL_METADATA_VERSION,
    }


def is_canonical(document: dict[str, Any]) -> bool:
    """Return True if a document dict carries all canonical fields."""
    return CANONICAL_FIELDS.issubset(document.keys())


def missing_canonical_fields(document: dict[str, Any]) -> frozenset[str]:
    """Return the set of canonical fields absent from a document dict."""
    return CANONICAL_FIELDS - document.keys()
