"""Tests for structured logging + request tracing."""
import json
import logging

from app.config import settings
from app.observability import RequestIDMiddleware, configure_logging, get_logger


def test_request_carries_request_id_header(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.headers.get(settings.request_id_header)


def test_configure_logging_json_emits_parseable_line(monkeypatch, capsys):
    monkeypatch.setattr(settings, "log_json", True)
    configure_logging()
    try:
        get_logger("fitlens.test").info(
            "hello", extra={"request_id": "abc-123", "status_code": 200}
        )
        for handler in logging.getLogger().handlers:
            handler.flush()
        line = capsys.readouterr().err.strip().splitlines()[-1]
        record = json.loads(line)
        assert record["message"] == "hello"
        assert record["level"] == "INFO"
        assert record["logger"] == "fitlens.test"
        assert record["request_id"] == "abc-123"
        assert record["status_code"] == 200
        assert "timestamp" in record
    finally:
        # Restore the dev (human) formatter for other tests.
        monkeypatch.setattr(settings, "log_json", False)
        configure_logging()


def test_middleware_sets_request_state_request_id():
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient

    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/probe")
    def probe(request: Request) -> dict:
        # RequestIDMiddleware ran first and stashed the id on request.state.
        return {"request_id": request.state.request_id}

    with TestClient(app) as c:
        r = c.get("/probe")
    assert r.status_code == 200
    body = r.json()
    assert body["request_id"]
    # The same id is echoed back in the response header.
    assert r.headers.get(settings.request_id_header) == body["request_id"]


def test_configure_logging_is_idempotent():
    configure_logging()
    before = len(logging.getLogger().handlers)
    configure_logging()
    configure_logging()
    after = len(logging.getLogger().handlers)
    assert after == before
