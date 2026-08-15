from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from concurrency_bench.infrastructure.config import Settings
from concurrency_bench.infrastructure.database.base import Base


def build_engine(database_url: str | None = None) -> Engine:
    return create_engine(_resolve_database_url(database_url), future=True, pool_pre_ping=True)


def build_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    engine = build_engine(database_url)
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def reset_schema(engine: Engine) -> None:
    from concurrency_bench.infrastructure.database import models as _models  # noqa: F401

    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        with conn.begin():
            try:
                conn.execute(
                    text("ALTER TABLE experiment_results ADD COLUMN IF NOT EXISTS strategy_name VARCHAR(100)")
                )
            except Exception:
                pass


def _resolve_database_url(database_url: str | None) -> str:
    if database_url is not None:
        return _normalize_driver(database_url)

    try:
        return _normalize_driver(Settings.from_env().database_url)
    except ValueError:
        return "postgresql+psycopg://concurrency_bench:concurrency_bench@localhost:5432/concurrency_bench"


def _normalize_driver(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url[len("postgresql://"):]
    return database_url
