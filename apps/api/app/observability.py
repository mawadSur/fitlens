"""Structured logging + request tracing for FitLens.

`configure_logging()` installs a formatter on the root logger (JSON in prod,
concise human-readable in dev) and is safe to call repeatedly. `RequestIDMiddleware`
tags every request with a request id, measures wall-clock duration, and logs a
one-line access record.
"""
from __future__ import annotations

import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .config import settings

# Marker so configure_logging() can find/replace its own handler idempotently.
_HANDLER_TAG = "fitlens"

# Reserved LogRecord attributes — anything else on the record is an "extra" field.
_RESERVED = set(
    logging.makeLogRecord({}).__dict__
) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    """One JSON object per line: timestamp, level, logger, message + extras."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def _build_handler() -> logging.Handler:
    handler = logging.StreamHandler()
    handler.set_name(_HANDLER_TAG)
    if settings.log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-7s %(name)s — %(message)s")
        )
    return handler


def configure_logging() -> None:
    """Install our handler on the root logger. Idempotent."""
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    # Drop any handler we previously installed so re-calling re-reads settings.
    for existing in list(root.handlers):
        if existing.get_name() == _HANDLER_TAG:
            root.removeHandler(existing)
    root.addHandler(_build_handler())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a request id, time the request, log an access record."""

    async def dispatch(self, request: Request, call_next):
        header = settings.request_id_header
        request_id = request.headers.get(header) or str(uuid.uuid4())
        request.state.request_id = request_id

        logger = get_logger("fitlens.access")
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "request_id": request_id,
                },
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers[header] = request_id
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "request_id": request_id,
            },
        )
        return response
