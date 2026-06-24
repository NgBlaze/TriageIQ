"""
Database engine, session management, and schema initialization.

Uses SQLAlchemy so the same code runs against SQLite locally (zero setup) and
PostgreSQL in deployment (e.g. Neon/Supabase free tier) — the only difference
is the DATABASE_URL. The app logic never talks to the engine directly; it goes
through the repository layer (app/services/repository.py) and the get_db
dependency below.
"""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _normalize_db_url(url: str) -> str:
    """Normalize provider-specific URL quirks.

    Some hosts (Neon, Heroku) hand out `postgres://` URLs, but SQLAlchemy's
    driver name is `postgresql://`. Normalizing here means deployment config
    can paste the provider's URL verbatim.
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


_db_url = _normalize_db_url(settings.database_url)

# check_same_thread is a SQLite-only concern: FastAPI may use the session from a
# different thread than it was created on. Harmless/irrelevant for Postgres.
_connect_args = {"check_same_thread": False} if _db_url.startswith("sqlite") else {}

engine = create_engine(_db_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    """Create tables that don't yet exist.

    Sufficient for this project's scope (single additive schema); a real
    production system would use Alembic migrations instead.
    """
    # Import models so they register on Base.metadata before create_all.
    from app.models import db_models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a DB session, closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
