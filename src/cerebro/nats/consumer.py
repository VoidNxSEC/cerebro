"""
Cerebro NATS consumer.

Subscribes to ``ingest.file.sanitized.v1`` published after a file passes the
DAG pipeline.  For each event, runs knowledge extraction and publishes a
``cognition.insight.generated.v1`` event back onto the bus.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger("cerebro.nats.consumer")

_subscription = None
_nc = None


async def start_consumer() -> None:
    """Subscribe to ingest.file.sanitized.v1 and process incoming events."""
    global _subscription, _nc
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    nkey_seed = os.environ.get("NATS_NKEY_SEED", "").strip()
    try:
        import nats
        kwargs = {}
        if nkey_seed:
            kwargs["nkeys_seed"] = nkey_seed.encode()
        _nc = await nats.connect(nats_url, **kwargs)
        _subscription = await _nc.subscribe(
            "ingest.file.sanitized.v1",
            cb=_handle_sanitized_file,
        )
        logger.info(
            "NATS consumer subscribed to ingest.file.sanitized.v1 @ %s", nats_url
        )
        while True:
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        logger.warning("NATS consumer failed (non-fatal): %s", exc)


async def stop_consumer() -> None:
    """Unsubscribe and drain the consumer connection."""
    global _subscription, _nc
    if _subscription is not None:
        try:
            await _subscription.unsubscribe()
        except Exception:
            pass
        _subscription = None
    if _nc is not None and not _nc.is_closed:
        try:
            await _nc.drain()
        except Exception:
            pass
        _nc = None


async def _handle_sanitized_file(msg) -> None:
    """Process ingest.file.sanitized.v1 — extract knowledge, publish insight."""
    try:
        payload = json.loads(msg.data.decode())
        correlation_id = payload.get("event_id", str(uuid.uuid4()))
        file_path = payload.get("file_path", "")
        file_hash = payload.get("file_hash_sha256", "")
        original_filename = payload.get("original_filename", "")
        mime_type = payload.get("mime_type", "")

        logger.info(
            "Processing sanitized file: %s (hash=%s)", original_filename, file_hash[:12]
        )

        # Run extraction in executor so we don't block the event loop
        loop = asyncio.get_running_loop()
        themes, concepts, summary, artifacts_count = await loop.run_in_executor(
            None,
            _extract_knowledge,
            file_path,
            original_filename,
            mime_type,
        )

        # Publish insight
        from cerebro.nats.publisher import publish_insight

        insight_payload = {
            "event_id": str(uuid.uuid4()),
            "source_service": "cerebro",
            "correlation_id": correlation_id,
            "file_hash": file_hash,
            "artifacts_count": artifacts_count,
            "themes": themes,
            "concepts": concepts,
            "summary": summary,
            "embedding_dims": 384,  # default sentence-transformers dim
            "indexed_to_chromadb": False,  # ChromaDB indexing is separate
            "timestamp": datetime.now(UTC).isoformat(),
        }
        await publish_insight(insight_payload)
        logger.info(
            "Published cognition.insight.generated.v1 for %s (%d themes, %d concepts)",
            original_filename,
            len(themes),
            len(concepts),
        )

    except Exception as exc:
        logger.error("Error handling sanitized file event: %s", exc)


def _extract_knowledge(
    file_path: str,
    original_filename: str,
    mime_type: str,
) -> tuple[list[str], list[str], str, int]:
    """
    Synchronous knowledge extraction from a file.

    Returns (themes, concepts, summary, artifacts_count).
    Falls back gracefully if the file is not accessible.
    """
    themes: list[str] = []
    concepts: list[str] = []
    summary = ""
    artifacts_count = 0

    path = Path(file_path) if file_path else None
    ext = Path(original_filename).suffix.lower() if original_filename else ""

    # Attempt code analysis for supported source files
    code_extensions = {".py", ".rs", ".go", ".ts", ".js", ".nix", ".sh", ".bash"}
    if ext in code_extensions and path and path.exists():
        try:
            from cerebro.core.extraction.analyze_code import HermeticAnalyzer

            analyzer = HermeticAnalyzer()
            artifacts = analyzer.analyze_file(path)
            artifacts_count = len(artifacts) if artifacts else 0
            for artifact in artifacts or []:
                if artifact.artifact_type and artifact.artifact_type not in themes:
                    themes.append(artifact.artifact_type)
                if artifact.name and artifact.name not in concepts:
                    concepts.append(artifact.name)
            if artifacts_count > 0:
                summary = (
                    f"Analyzed {original_filename}: "
                    f"{artifacts_count} code artifacts extracted."
                )
        except Exception as exc:
            logger.debug("Code analysis failed for %s: %s", original_filename, exc)

    # Text-based heuristic extraction
    if not summary and path and path.exists():
        try:
            text = path.read_text(errors="ignore")[:4096]
            words = [w.strip(".,;:()[]{}\"'") for w in text.split() if len(w) > 4]
            # Deduplicate and take most common as concepts
            seen: dict[str, int] = {}
            for w in words:
                wl = w.lower()
                seen[wl] = seen.get(wl, 0) + 1
            top = sorted(seen.items(), key=lambda x: -x[1])[:20]
            concepts = list({k for k, _ in top[:15]})
            artifacts_count = max(artifacts_count, len(words) // 50)
            summary = (
                f"Extracted text from {original_filename}: "
                f"{len(words)} meaningful words, {len(concepts)} key concepts."
            )
            themes = _infer_themes(mime_type, ext)
        except Exception as exc:
            logger.debug("Text extraction failed for %s: %s", original_filename, exc)

    if not themes:
        themes = _infer_themes(mime_type, ext)
    if not summary:
        summary = f"File {original_filename} processed by Cerebro pipeline."

    return themes, concepts, summary, artifacts_count


def _infer_themes(mime_type: str, ext: str) -> list[str]:
    """Infer document themes from MIME type and file extension."""
    themes = []
    if mime_type.startswith("text/"):
        themes.append("text")
    if "python" in mime_type or ext == ".py":
        themes.extend(["code", "python"])
    elif ext in (".rs",):
        themes.extend(["code", "rust"])
    elif ext in (".go",):
        themes.extend(["code", "go"])
    elif ext in (".ts", ".js"):
        themes.extend(["code", "typescript"])
    elif mime_type == "application/pdf" or ext == ".pdf":
        themes.extend(["document", "pdf"])
    elif ext in (".md", ".rst", ".txt"):
        themes.extend(["documentation"])
    elif ext in (".nix",):
        themes.extend(["configuration", "nix"])
    elif ext in (".yaml", ".yml", ".toml", ".json"):
        themes.extend(["configuration"])
    elif ext in (".sh", ".bash"):
        themes.extend(["code", "shell"])
    return list(dict.fromkeys(themes))  # deduplicate preserving order
