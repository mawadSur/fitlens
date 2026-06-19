"""Pytest fixtures — isolated temp SQLite DB, seeded once per session."""
import os
import pathlib
import tempfile

# Must be set before any `app` import so the engine binds to the test DB.
_TEST_DB = pathlib.Path(tempfile.gettempdir()) / "fitlens_test.db"
_TEST_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"

import pytest  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.seed import force_reseed  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _seeded():
    force_reseed()
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
