"""Structured logging configuration for deterministic startup and runtime logs."""
from __future__ import annotations

import json
import logging
import os
import socket
import time
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class StructuredLogRecord:
    """Serializable log record container."""

    timestamp: float
    level: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        payload = {
            "ts": round(self.timestamp, 3),
            "level": self.level,
            "msg": self.message,
            **self.context,
        }
        return json.dumps(payload, sort_keys=True)


class JsonLogFormatter(logging.Formatter):
    """Formatter that emits structured JSON for deterministic log comparisons."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        enriched = StructuredLogRecord(
            timestamp=record.created,
            level=record.levelname,
            message=record.getMessage(),
            context={
                "module": record.module,
                "hostname": socket.gethostname(),
                "pid": os.getpid(),
            },
        )
        return enriched.to_json()


def configure_logging(level: str = "INFO") -> None:
    """Configure application-wide structured logging."""

    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())

    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), handlers=[handler])
    logging.getLogger(__name__).debug("Structured logging configured", extra={"stage": "startup"})


def startup_banner(app_name: str, stage: str = "cold_start") -> None:
    """Emit a deterministic startup banner for benchmarks."""

    logger = logging.getLogger(app_name)
    logger.info(
        "startup",
        extra={
            "stage": stage,
            "time": round(time.time(), 3),
        },
    )
