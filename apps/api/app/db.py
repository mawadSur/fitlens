"""Database engine/session. SQLite for dev, Postgres for prod via DATABASE_URL."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


_is_sqlite = settings.database_url.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _is_sqlite else {}
# SQLite keeps its original (poolless) behavior; pooling args apply only to
# real client/server databases (Postgres et al.) where they're meaningful.
_pool_kwargs = (
    {}
    if _is_sqlite
    else {
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_pre_ping": settings.db_pool_pre_ping,
    }
)
engine = create_engine(
    settings.database_url, connect_args=_connect_args, future=True, **_pool_kwargs
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Dev bootstrap. Production uses Alembic migrations (see alembic/)."""
    from . import models  # noqa: F401  ensure models are registered

    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
