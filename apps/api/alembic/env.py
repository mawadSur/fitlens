"""Alembic environment.

Wires Alembic into the FitLens app: puts the app package on sys.path so the
domain models import, uses ``Base.metadata`` as the autogenerate target, and
overrides ``alembic.ini``'s placeholder URL with ``settings.database_url`` so
migrations always run against the same database as the application.
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make the `app` package importable when running `alembic` from apps/api.
_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.config import settings  # noqa: E402
from app.db import Base  # noqa: E402
from app import models  # noqa: E402,F401  registers all tables on Base.metadata

# Alembic Config object; provides access to values in alembic.ini.
config = context.config

# Follow the same environment as the app, so migrations and the app point at
# the same database. A test/CLI override may be passed via `-x db_url=...`
# (e.g. `alembic -x db_url=sqlite:///tmp/x.db upgrade head`); when absent we
# fall back to settings.database_url. The app itself never passes `-x`.
_x_args = context.get_x_argument(as_dictionary=True)
_db_url = _x_args.get("db_url") or settings.database_url
config.set_main_option("sqlalchemy.url", _db_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for 'autogenerate' support — every table registered on Base.
target_metadata = Base.metadata


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a DBAPI connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Batch mode lets SQLite emulate ALTER TABLE via table copy.
        render_as_batch=_is_sqlite(url or ""),
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        url = str(connection.engine.url)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Batch mode lets SQLite emulate ALTER TABLE via table copy.
            render_as_batch=_is_sqlite(url),
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
