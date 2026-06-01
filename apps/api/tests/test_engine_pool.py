"""The DB_POOL_SIZE lever (db/engine.make_engine).

Default (0) keeps NullPool, a fresh Neon/PgBouncer connection per checkout,
which is multi-loop safe. A positive size opts into a warm pool that reuses
connections on the single server event loop, cutting the per-request connect
round trip. Engine construction is lazy (no connection), so this asserts the
pool wiring without touching a database.
"""

from __future__ import annotations

from sqlalchemy.pool import NullPool

from laytimely_api.db.engine import make_engine

_ASYNCPG_URL = "postgresql+asyncpg://u:p@example.invalid:5432/db"


def test_default_pool_size_uses_nullpool() -> None:
    engine = make_engine(_ASYNCPG_URL)  # pool_size defaults to 0
    assert isinstance(engine.pool, NullPool)


def test_positive_pool_size_uses_warm_pool() -> None:
    engine = make_engine(_ASYNCPG_URL, pool_size=5)
    assert not isinstance(engine.pool, NullPool)
    # The pool advertises the configured capacity.
    assert engine.pool.size() == 5
