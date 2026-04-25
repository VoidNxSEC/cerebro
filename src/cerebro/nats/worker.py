"""
Cerebro ingest worker — Spectre Fleet protocol.

Pulls `rag.index.v1` messages from the CEREBRO_INGEST JetStream stream,
runs the configured VectorStoreProvider upsert, and publishes a
`document.indexed.v1.<correlation_id>` reply on core NATS.

Each worker identifies itself as source_service `cerebro-ingest-worker-<id>`.
Multiple workers can run concurrently — the `cerebro-ingest-worker` durable
consumer distributes messages among them with at-least-once semantics.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import uuid
from datetime import datetime, timezone
from typing import Any

from cerebro.core.metadata import build_canonical_fields
from cerebro.nats.ingest import IngestRequest
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
from cerebro.providers.vector_store_factory import build_vector_store_provider

logger = logging.getLogger("cerebro.nats.worker")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class IngestWorker:
    """
    JetStream pull-consumer worker that materializes ingest requests.

    Binds to the `cerebro-ingest-worker` durable consumer (created on first
    boot). Subsequent workers share the same durable and form a consumer group.
    """

    def __init__(
        self,
        *,
        worker_id: str | None = None,
        provider_override: str | None = None,
        nats_config: NatsConfig | None = None,
        batch: int = 10,
        fetch_timeout: float = 5.0,
    ) -> None:
        self.worker_id = worker_id or os.environ.get("CEREBRO_WORKER_ID") or str(uuid.uuid4())[:8]
        self.provider_override = provider_override
        self.nats_config = nats_config or NatsConfig.from_env()
        self.batch = batch
        self.fetch_timeout = fetch_timeout
        self._stop = asyncio.Event()
        self._service_id = f"cerebro-ingest-worker-{self.worker_id}"

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    def request_stop(self) -> None:
        self._stop.set()

    async def run(self) -> None:
        """Main loop: pull batches, process, ack, repeat until stop signal."""

        from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy

        nc = await connect(self.nats_config)
        try:
            await ensure_ingest_stream(nc)
            js = nc.jetstream()

            consumer_config = ConsumerConfig(
                durable_name=INGEST_WORKER_DURABLE,
                ack_policy=AckPolicy.EXPLICIT,
                deliver_policy=DeliverPolicy.ALL,
                max_deliver=5,
                ack_wait=60,
                filter_subject=INGEST_REQUEST_SUBJECT,
            )
            # Idempotent: create if missing, else reuse.
            try:
                await js.add_consumer(INGEST_STREAM_NAME, consumer_config)
            except Exception as exc:
                logger.debug("Consumer already exists or add failed (%s); continuing.", exc)

            psub = await js.pull_subscribe(
                INGEST_REQUEST_SUBJECT,
                durable=INGEST_WORKER_DURABLE,
                stream=INGEST_STREAM_NAME,
            )

            logger.info(
                "IngestWorker %s started (service=%s, durable=%s)",
                self.worker_id,
                self._service_id,
                INGEST_WORKER_DURABLE,
            )

            while not self._stop.is_set():
                try:
                    messages = await psub.fetch(batch=self.batch, timeout=self.fetch_timeout)
                except asyncio.TimeoutError:
                    continue
                except Exception as exc:
                    logger.warning("IngestWorker %s fetch failed: %s", self.worker_id, exc)
                    await asyncio.sleep(1.0)
                    continue

                for msg in messages:
                    await self._handle_message(nc, msg)

            logger.info("IngestWorker %s stopping.", self.worker_id)
        finally:
            await nc.drain()

    # ------------------------------------------------------------------
    # message handling
    # ------------------------------------------------------------------

    async def _handle_message(self, nc, msg) -> None:
        correlation_id: str | None = None
        try:
            # Spectre envelope: event_id, event_type, correlation_id, payload, ...
            envelope = json.loads(msg.data.decode())
            correlation_id = envelope.get("correlation_id") or str(uuid.uuid4())
            payload = envelope.get("payload") or {}

            documents = payload.get("documents") or []
            embeddings = payload.get("embeddings")
            namespace = payload.get("namespace")
            provider_name = self.provider_override or payload.get("provider")

            enriched = [self._enrich(doc, namespace) for doc in documents]

            # Deduplicate within the message batch by content_hash.
            seen: dict[str, dict] = {}
            for doc in enriched:
                seen[doc["content_hash"]] = doc
            unique = list(seen.values())
            if len(unique) < len(enriched):
                logger.debug(
                    "IngestWorker %s dedup: %d → %d unique chunks (correlation_id=%s).",
                    self.worker_id, len(enriched), len(unique), correlation_id,
                )
            if embeddings:
                # Re-align embeddings to deduplicated order if lengths differ.
                if len(embeddings) == len(enriched) and len(unique) < len(enriched):
                    hash_to_idx = {doc["content_hash"]: i for i, doc in enumerate(enriched)}
                    embeddings = [embeddings[hash_to_idx[doc["content_hash"]]] for doc in unique]

            inserted = await asyncio.get_running_loop().run_in_executor(
                None,
                self._upsert,
                unique,
                embeddings,
                namespace,
                provider_name,
            )

            await self._publish_completion(
                nc,
                correlation_id,
                status="success",
                inserted=inserted,
            )
            await msg.ack()
            logger.info(
                "IngestWorker %s processed correlation_id=%s (inserted=%d)",
                self.worker_id,
                correlation_id,
                inserted,
            )
        except Exception as exc:
            logger.exception("IngestWorker %s failed on correlation_id=%s", self.worker_id, correlation_id)
            if correlation_id:
                try:
                    await self._publish_completion(
                        nc,
                        correlation_id,
                        status="error",
                        inserted=0,
                        error=str(exc),
                    )
                except Exception:
                    logger.exception("Failed to publish error completion.")
            try:
                await msg.nak()
            except Exception:
                pass

    def _enrich(self, document: dict[str, Any], namespace: str | None) -> dict[str, Any]:
        """Populate canonical metadata fields so every row has content_hash/chunk_id."""

        merged = dict(document)
        content = str(merged.get("content") or merged.get("text") or "")
        doc_id = str(merged.get("id") or merged.get("chunk_id") or "")
        chunk_index = merged.get("chunk_index")
        canonical = build_canonical_fields(
            content=content,
            doc_id=doc_id,
            namespace=namespace,
            chunk_index=int(chunk_index) if chunk_index is not None else None,
        )
        for k, v in canonical.items():
            merged.setdefault(k, v)
        return merged

    def _upsert(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[list[float]] | None,
        namespace: str | None,
        provider_name: str | None,
    ) -> int:
        provider = build_vector_store_provider(provider_name)
        if not embeddings:
            raise ValueError(
                "IngestWorker received a request without pre-computed embeddings. "
                "Embedding computation on the worker is not implemented yet."
            )
        if len(embeddings) != len(documents):
            raise ValueError(
                f"Embeddings length {len(embeddings)} != documents length {len(documents)}."
            )
        return int(provider.upsert_documents(documents, embeddings, namespace=namespace))

    async def _publish_completion(
        self,
        nc,
        correlation_id: str,
        *,
        status: str,
        inserted: int = 0,
        error: str | None = None,
    ) -> None:
        """Publish a Spectre document.indexed.v1 event as the completion signal."""
        subject = completion_subject(correlation_id)
        envelope = {
            "event_id": str(uuid.uuid4()),
            "event_type": "document.indexed.v1",
            "timestamp": _now_iso(),
            "source_service": self._service_id,
            "correlation_id": correlation_id,
            "payload": {
                "status": status,
                "inserted": inserted,
                "error": error,
            },
            "metadata": {
                "trace_id": str(uuid.uuid4()),
            },
        }
        await nc.publish(subject, json.dumps(envelope).encode())
        await nc.flush()


def _run_worker() -> None:
    """Module entrypoint: `python -m cerebro.nats.worker`."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    worker = IngestWorker()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _shutdown(*_args: Any) -> None:
        logger.info("Shutdown signal received.")
        worker.request_stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown)
        except (NotImplementedError, RuntimeError):
            signal.signal(sig, _shutdown)

    try:
        loop.run_until_complete(worker.run())
    finally:
        loop.close()


if __name__ == "__main__":
    _run_worker()
