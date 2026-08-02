"""
Cerebro NATS publisher.

Publishes cognition.insight.generated.v1 events after knowledge extraction.
"""

import asyncio
import json
import logging
import os

logger = logging.getLogger("cerebro.nats.publisher")

_nc = None
_loop = None


async def connect() -> bool:
    """Connect to NATS. Non-fatal on failure."""
    global _nc, _loop
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    nkey_seed = os.environ.get("NATS_NKEY_SEED", "").strip()
    try:
        import nats
        _loop = asyncio.get_running_loop()
        kwargs = {}
        if nkey_seed:
            kwargs["nkeys_seed"] = nkey_seed.encode()
        _nc = await nats.connect(nats_url, **kwargs)
        logger.info("NATS publisher connected: %s (nkey=%s)", nats_url, bool(nkey_seed))
        return True
    except Exception as exc:
        logger.warning("NATS publisher connection failed (non-fatal): %s", exc)
        return False


async def drain() -> None:
    """Drain and close the NATS publisher connection."""
    global _nc
    if _nc is not None and not _nc.is_closed:
        try:
            await _nc.drain()
        except Exception as exc:
            logger.warning("NATS publisher drain failed: %s", exc)
    _nc = None


async def publish_insight(payload: dict) -> None:
    """Publish a cognition.insight.generated.v1 event."""
    if _nc is None:
        return
    try:
        data = json.dumps(payload).encode()
        await _nc.publish("cognition.insight.generated.v1", data)
        logger.debug(
            "Published cognition.insight.generated.v1 (correlation_id=%s)",
            payload.get("correlation_id", "?"),
        )
    except Exception as exc:
        logger.warning("NATS publish failed (non-fatal): %s", exc)
