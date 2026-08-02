"""Cerebro NATS integration — Spectre Fleet protocol.

Event taxonomy:
  rag.index.v1                           — ingest request (JetStream)
  document.indexed.v1.<correlation_id>   — completion reply (core NATS)
"""

from cerebro.nats.ingest import (
    IngestCompletion,
    IngestRequest,
    publish_ingest_request,
)
from cerebro.nats.streams import (
    CEREBRO_SERVICE_ID,
    INGEST_REQUEST_SUBJECT,
    INGEST_STREAM_NAME,
    INGEST_WORKER_DURABLE,
    NatsConfig,
    completion_subject,
    connect,
    ensure_ingest_stream,
)
from cerebro.nats.worker import IngestWorker

__all__ = [
    "IngestCompletion",
    "IngestRequest",
    "IngestWorker",
    "NatsConfig",
    "CEREBRO_SERVICE_ID",
    "INGEST_REQUEST_SUBJECT",
    "INGEST_STREAM_NAME",
    "INGEST_WORKER_DURABLE",
    "completion_subject",
    "connect",
    "ensure_ingest_stream",
    "publish_ingest_request",
]
