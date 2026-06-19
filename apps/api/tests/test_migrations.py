"""Hermetic Alembic migration test.

Runs the migrations against a brand-new temp SQLite database via Alembic's
Python API and asserts the resulting schema matches Base.metadata. It builds
its OWN engine and DB file and never touches the shared fitlens_test.db that
conftest seeds for the rest of the suite.
"""
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.db import Base
from app import models  # noqa: F401  ensure all 9 tables register on Base.metadata

# apps/api root: tests/ -> api/
_API_ROOT = Path(__file__).resolve().parents[1]
_ALEMBIC_INI = _API_ROOT / "alembic.ini"
_ALEMBIC_DIR = _API_ROOT / "alembic"

EXPECTED_TABLES = frozenset(Base.metadata.tables)


def _make_config(db_url: str) -> Config:
    """Alembic Config wired to a specific (throwaway) database URL.

    env.py prefers the `-x db_url=...` override over settings.database_url, so
    we pass the temp URL through cmd_opts. This avoids importing or mutating the
    app engine, keeping the seeded test DB untouched.
    """
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_ALEMBIC_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    # Emulate `alembic -x db_url=<url>` so env.py picks up the override.
    cfg.cmd_opts = argparse.Namespace(x=[f"db_url={db_url}"])
    return cfg


@pytest.fixture
def temp_db():
    """A fresh temp sqlite file + URL, removed afterward."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="fitlens_migtest_")
    os.close(fd)
    os.unlink(path)  # let Alembic/SQLite create it fresh
    url = f"sqlite:///{path}"
    try:
        yield url, path
    finally:
        Path(path).unlink(missing_ok=True)


def test_upgrade_head_creates_all_tables(temp_db):
    url, path = temp_db
    cfg = _make_config(url)

    command.upgrade(cfg, "head")

    # Reflect with our OWN engine (never app.db.engine).
    engine = create_engine(url, future=True)
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    missing = EXPECTED_TABLES - tables
    assert not missing, f"migration did not create: {sorted(missing)}"
    # All 9 domain tables, including users.
    assert "users" in tables
    assert len(EXPECTED_TABLES) == 9


def test_downgrade_base_drops_all_tables(temp_db):
    url, path = temp_db
    cfg = _make_config(url)

    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    engine = create_engine(url, future=True)
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    remaining = EXPECTED_TABLES & tables
    assert not remaining, f"downgrade left tables behind: {sorted(remaining)}"
