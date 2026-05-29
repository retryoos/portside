"""Async engine + session factory for the relational store.

SQLite gets ``PRAGMA foreign_keys=ON`` so FK cascades behave like Postgres.
``create_all`` is the test/dev schema bootstrap; production runs Alembic.
"""

from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .models import Base


def make_engine(database_url: str) -> AsyncEngine:
    engine = create_async_engine(database_url, future=True)
    if database_url.startswith("sqlite"):

        @event.listens_for(engine.sync_engine, "connect")
        def _enable_sqlite_fk(dbapi_conn, _record):  # noqa: ANN001
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return engine


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False keeps loaded attributes usable after commit.
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def create_all(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def run_migrations(database_url: str) -> None:
    """Run ``alembic upgrade head`` against ``database_url`` (synchronous).

    Call from a worker thread when inside a running event loop (the Alembic env
    spins up its own loop): ``await asyncio.to_thread(run_migrations, url)``.
    """
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    api_root = Path(__file__).resolve().parents[2]  # apps/api
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(cfg, "head")
