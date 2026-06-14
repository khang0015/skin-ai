from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ..config import settings


class Base(DeclarativeBase):
    pass


def is_database_configured() -> bool:
    return bool(settings.database_url.strip())


def _make_engine():
    if not is_database_configured():
        return None

    # SQLite doesn't support pool_size / max_overflow
    is_sqlite = settings.database_url.startswith("sqlite")
    kwargs = {
        "pool_pre_ping": True,
        "future": True,
    }
    if not is_sqlite:
        kwargs["pool_size"] = settings.db_pool_size
        kwargs["max_overflow"] = settings.db_max_overflow
        kwargs["pool_timeout"] = settings.db_pool_timeout

    return create_engine(settings.database_url, **kwargs)


engine = _make_engine()

SessionLocal = (
    sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    if engine is not None
    else None
)


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured.")
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
