"""
cerebro.core.utils.logging
───────────────────────────
Structured logger factory — replaces scattered print() calls.

Supports two modes:
  - LOCAL:      pretty console output with colors (dev)
  - STRUCTURED: vendor-neutral JSON with severity (prod / any log aggregator)

Usage:
    from cerebro.core.utils.logging import get_logger

    logger = get_logger("cerebro.rag.engine")
    logger.info("Query processed", query=query, latency_ms=42.3, k=5)
"""

import datetime
import json
import logging
import os
import sys
from typing import Any

# ─── Environment detection ───────────────────────────────────────────────────

def _is_structured_env() -> bool:
    """Return True when running in a container / CI / any non-TTY environment."""
    import sys
    return bool(
        os.getenv("K_SERVICE")        # Cloud Run
        or os.getenv("K_REVISION")    # Cloud Run revision
        or os.getenv("CI")            # CI pipelines
        or os.getenv("CEREBRO_JSON_LOGS")  # explicit override
        or not sys.stdout.isatty()    # piped / non-interactive
    )

def _is_rich_available() -> bool:
    try:
        import rich  # noqa
        return True
    except ImportError:
        return False


# ─── Formatters ─────────────────────────────────────────────────────────────

class StructuredFormatter(logging.Formatter):
    """
    Vendor-neutral JSON structured logging.
    Works with any log aggregator (Loki, Elasticsearch, Datadog, Cloud Logging…).
    Uses plain keys — no vendor-specific prefixes.
    """
    SEVERITY_MAP = {
        logging.DEBUG:    "DEBUG",
        logging.INFO:     "INFO",
        logging.WARNING:  "WARNING",
        logging.ERROR:    "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "severity":  self.SEVERITY_MAP.get(record.levelno, "DEFAULT"),
            "message":   record.getMessage(),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "logger":    record.name,
            "source_location": {
                "file":     record.pathname,
                "line":     record.lineno,
                "function": record.funcName,
            },
        }
        # Extra fields passed as kwargs in the log call
        for key, val in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "levelname", "levelno",
                "pathname", "filename", "module", "exc_info",
                "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "message",
            ):
                payload[key] = val

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


# Keep backward-compat alias so any existing import of CloudRunFormatter still works
CloudRunFormatter = StructuredFormatter


class LocalFormatter(logging.Formatter):
    """
    Human-readable colored output for local development.
    Falls back to plain text if no TTY.
    """
    LEVEL_COLORS = {
        "DEBUG":    "\033[36m",   # cyan
        "INFO":     "\033[32m",   # green
        "WARNING":  "\033[33m",   # yellow
        "ERROR":    "\033[31m",   # red
        "CRITICAL": "\033[35m",   # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color  = self.LEVEL_COLORS.get(record.levelname, "")
        reset  = self.RESET
        ts     = datetime.datetime.now().strftime("%H:%M:%S")
        name   = record.name.replace("cerebro.", "⬡ ")
        msg    = record.getMessage()

        # Campos extras inline
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in (
                "name", "msg", "args", "levelname", "levelno",
                "pathname", "filename", "module", "exc_info",
                "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "message",
                "taskName",
            )
        }
        extra_str = "  " + "  ".join(f"{k}={v}" for k, v in extras.items()) if extras else ""

        line = f"{color}[{ts}] {record.levelname:<8}{reset} {name}: {msg}{extra_str}"

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)

        return line


# ─── Logger factory ─────────────────────────────────────────────────────────

_configured_loggers: set[str] = set()

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Main factory. Returns a logger configured for the current environment.

    Examples:
        logger = get_logger("cerebro.rag.engine")
        logger = get_logger("cerebro.gcp.billing", level=logging.DEBUG)
    """
    logger = logging.getLogger(name)

    if name in _configured_loggers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if _is_structured_env():
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(LocalFormatter())

    logger.addHandler(handler)
    _configured_loggers.add(name)
    return logger


def configure_root(level: int = logging.INFO):
    """
    Configure the root cerebro logger.
    Call once in cli.py or launcher.py at startup.
    """
    root = get_logger("cerebro", level=level)
    return root


# ─── StructuredLogger wrapper ────────────────────────────────────────────────

class StructuredLogger:
    """
    Thin wrapper that accepts kwargs as structured fields.
    structlog-style API without the dependency.

    logger = StructuredLogger("cerebro.rag")
    logger.info("retrieved", k=20, latency_ms=12.4, reranked=True)
    """

    def __init__(self, name: str, level: int = logging.INFO):
        self._log = get_logger(name, level)

    def _emit(self, level: int, msg: str, **kwargs):
        if kwargs:
            extra = {k: v for k, v in kwargs.items()}
            record = self._log.makeRecord(
                self._log.name, level, "(unknown)", 0,
                msg, (), None, extra=extra
            )
            self._log.handle(record)
        else:
            self._log.log(level, msg)

    def debug(self,    msg: str, **kw): self._emit(logging.DEBUG,    msg, **kw)
    def info(self,     msg: str, **kw): self._emit(logging.INFO,     msg, **kw)
    def warning(self,  msg: str, **kw): self._emit(logging.WARNING,  msg, **kw)
    def error(self,    msg: str, **kw): self._emit(logging.ERROR,    msg, **kw)
    def critical(self, msg: str, **kw): self._emit(logging.CRITICAL, msg, **kw)
