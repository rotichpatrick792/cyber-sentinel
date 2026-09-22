"""SQLAlchemy engine, session factory, and declarative base.

One engine per process, one session per request. FastAPI dependencies
hand out sessions from the pool defined here.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# The engine manages a connection pool. Created once at import time.
# pool_pre_ping revalidates dead connections before use (Postgres restarts).
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_pre_ping=True,
    future=True,
)

# Session factory. Autocommit/autoflush off — modern SQLAlchemy 2.0 default.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
