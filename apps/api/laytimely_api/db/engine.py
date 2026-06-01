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
from sqlalchemy.pool import NullPool

from .models import Base


def make_engine(database_url: str) -> AsyncEngine:
    engine_kwargs: dict[str, object] = {"future": True}
    if "+asyncpg" in database_url:
        # Postgres-on-asyncpg config, tuned for Neon's pooled (PgBouncer,
        # transaction-pooling) endpoint:
        #   - NullPool: never reuse a connection across event loops. SQLAlchemy's
        #     default pool caches connections, and an asyncpg connection bound to
        #     one loop and reused on another raises "got Future attached to a
        #     different loop" (hit under asyncio.run() in tests and on cold-start
        #     work that runs on a different loop than request handling). A fresh
        #     connection per checkout sidesteps it; Neon fronts a pooler anyway.
        #   - statement_cache_size=0: PgBouncer transaction pooling is
        #     incompatible with asyncpg's server-side prepared-statement cache,
        #     which otherwise surfaces as intermittent 500s on query endpoints.
        engine_kwargs["poolclass"] = NullPool
        engine_kwargs["connect_args"] = {"statement_cache_size": 0}
    engine = create_async_engine(database_url, **engine_kwargs)
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
