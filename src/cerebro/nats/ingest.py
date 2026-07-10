"""
Cerebro ingestion over NATS JetStream — Spectre Fleet protocol.

Publishes `rag.index.v1` events (JetStream, persistent) and waits for
`document.indexed.v1.<correlation_id>` replies (core NATS, ephemeral).

Event envelope follows the Spectre schema:
  event_id, event_type, timestamp, source_service, correlation_id, payload, metadata
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from cerebro.nats.streams import (
    CEREBRO_SERVICE_ID,
    INGEST_REQUEST_SUBJECT,
    INGEST_STREAM_NAME,
    NatsConfig,
    completion_subject,
    connect,
    ensure_ingest_stream,
)

logger = logging.getLogger("cerebro.nats.ingest")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class IngestRequest:
    """A batch of documents to ingest through the distributed pipeline."""

    documents: list[dict[str, Any]]
    embeddings: list[list[float]] | None = None
    namespace: str | None = None
    provider: str | None = None
    # correlation_id links this request to its completion event
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_bytes(self) -> bytes:
        """Serialize as a Spectre rag.index.v1 event envelope."""
        envelope = {
            "event_id": str(uuid.uuid4()),
            "event_type": INGEST_REQUEST_SUBJECT,
            "timestamp": _now_iso(),
            "source_service": CEREBRO_SERVICE_ID,
            "correlation_id": self.correlation_id,
            "payload": {
                "documents": self.documents,
                "embeddings": self.embeddings,
                "namespace": self.namespace,
                "provider": self.provider,
            },
            "metadata": {
                "trace_id": str(uuid.uuid4()),
            },
        }
        return json.dumps(envelope).encode()


@dataclass
class IngestCompletion:
    """Result of an ingest request as reported by the worker."""

    correlation_id: str
    status: str  # "success" | "error"
    inserted: int = 0
    error: str | None = None
    worker_id: str | None = None

    @classmethod
    def from_bytes(cls, data: bytes) -> IngestCompletion:
        envelope = json.loads(data.decode())
        payload = envelope.get("payload") or {}
        return cls(
            correlation_id=envelope.get("correlation_id", ""),
            status=payload.get("status", "error"),
            inserted=int(payload.get("inserted", 0)),
            error=payload.get("error"),
            worker_id=envelope.get("source_service"),
        )


async def publish_ingest_request(
    request: IngestRequest,
    *,
    timeout: float = 30.0,
    config: NatsConfig | None = None,
) -> IngestCompletion:
    """
    Publish an ingest request and await completion.

    Subscribes to the completion subject BEFORE publishing to avoid the race
    where a very fast worker replies before our subscription is installed.
    """

    nc = await connect(config)
    try:
        await ensure_ingest_stream(nc)
        js = nc.jetstream()

        completion_future: asyncio.Future[IngestCompletion] = asyncio.get_running_loop().create_future()

        async def _on_completion(msg) -> None:
            if completion_future.done():
                return
            try:
                completion_future.set_result(IngestCompletion.from_bytes(msg.data))
            except Exception as exc:
                completion_future.set_exception(exc)

        subject = completion_subject(request.correlation_id)
        sub = await nc.subscribe(subject, cb=_on_completion)
        try:
            ack = await js.publish(
                INGEST_REQUEST_SUBJECT,
                request.to_bytes(),
                stream=INGEST_STREAM_NAME,
            )
            logger.info(
                "Published rag.index.v1 (correlation_id=%s, stream_seq=%s, docs=%d)",
                request.correlation_id,
                ack.seq,
                len(request.documents),
            )
            return await asyncio.wait_for(completion_future, timeout=timeout)
        finally:
            await sub.unsubscribe()
    finally:
        await nc.drain()
