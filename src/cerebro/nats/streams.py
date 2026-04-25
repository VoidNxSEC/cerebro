"""
Cerebro JetStream bootstrap.

Declares the persistent streams and consumer groups used for distributed
ingestion. Bootstrap is idempotent — calling `ensure_ingest_stream` twice is
safe; an existing stream with the same config is left alone, a drifted config
is updated in place.

Event taxonomy follows the Spectre Fleet protocol:
  rag.index.v1       — ingest/index request (JetStream, persistent)
  document.indexed.v1.<correlation_id> — per-request completion (core NATS, ephemeral)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger("cerebro.nats.streams")


INGEST_STREAM_NAME = "CEREBRO_INGEST"
INGEST_REQUEST_SUBJECT = "rag.index.v1"
INGEST_COMPLETED_SUBJECT_PREFIX = "document.indexed.v1"
INGEST_WORKER_DURABLE = "cerebro-ingest-worker"
CEREBRO_SERVICE_ID = "cerebro-rag"


def completion_subject(correlation_id: str) -> str:
    """Return the per-request completion subject (core NATS, not JetStream)."""
    return f"{INGEST_COMPLETED_SUBJECT_PREFIX}.{correlation_id}"


@dataclass(frozen=True, slots=True)
class NatsConfig:
    url: str
    nkey_seed: str | None = None

    @classmethod
    def from_env(cls) -> NatsConfig:
        return cls(
            url=os.environ.get("NATS_URL", "nats://localhost:4222"),
            nkey_seed=os.environ.get("NATS_NKEY_SEED", "").strip() or None,
        )


async def connect(config: NatsConfig | None = None):
    """Open a NATS connection. Raises on failure — callers decide how to recover."""

    import nats

    cfg = config or NatsConfig.from_env()
    kwargs: dict = {}
    if cfg.nkey_seed:
        kwargs["nkeys_seed"] = cfg.nkey_seed.encode()

    nc = await nats.connect(cfg.url, **kwargs)
    logger.info("NATS connected: %s", cfg.url)
    return nc


async def ensure_ingest_stream(nc) -> None:
    """Create or update the CEREBRO_INGEST JetStream stream (idempotent)."""

    from nats.js.api import RetentionPolicy, StorageType, StreamConfig
    from nats.js.errors import NotFoundError

    js = nc.jetstream()
    desired = StreamConfig(
        name=INGEST_STREAM_NAME,
        subjects=[INGEST_REQUEST_SUBJECT],
        retention=RetentionPolicy.WORK_QUEUE,
        storage=StorageType.FILE,
        max_msgs=-1,
        max_bytes=-1,
        max_age=0,
        num_replicas=1,
    )

    try:
        existing = await js.stream_info(INGEST_STREAM_NAME)
        if set(existing.config.subjects or []) != set(desired.subjects):
            await js.update_stream(config=desired)
            logger.info("JetStream stream %s updated.", INGEST_STREAM_NAME)
        else:
            logger.debug("JetStream stream %s already exists.", INGEST_STREAM_NAME)
    except NotFoundError:
        await js.add_stream(config=desired)
        logger.info("JetStream stream %s created.", INGEST_STREAM_NAME)
