"""Shared test fixtures.

API tests run against a real Postgres (the models use Postgres UUID/JSONB/enum
types, which SQLite can't emulate faithfully). The database URL is taken from
``TEST_DATABASE_URL`` if set, else the app's configured ``DATABASE_URL`` with
the host swapped to localhost so tests can run from the host against the
Compose Postgres. Tests that need the DB are skipped if it is unreachable.
"""

from __future__ import annotations

import os

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.db import Base, get_session
from app.main import app


def _test_database_url() -> str:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return explicit
    # Reach the Compose Postgres from the host. The mapped host port defaults to
    # 55432 (see the local .env); override with DB_PORT. Tests use a DEDICATED
    # database (bigfive_test) so create_all/drop_all never touch the app's data.
    port = os.environ.get("DB_PORT", "55432")
    db = os.environ.get("TEST_DB_NAME", "bigfive_test")
    return f"postgresql+asyncpg://bigfive:bigfive@localhost:{port}/{db}"


@pytest_asyncio.fixture
async def db_session():
    """Create all tables on a real Postgres, yield a session, then drop them.

    Skips the test if Postgres is unreachable so the suite still runs (health
    and forms tests do not need the DB) in environments without a database.
    """
    engine = create_async_engine(_test_database_url(), future=True)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:  # pragma: no cover - env-dependent
        await engine.dispose()
        pytest.skip(f"Postgres unavailable for DB test: {exc}")

    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    try:
        async with factory() as session:
            yield session
    finally:
        app.dependency_overrides.pop(get_session, None)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """An httpx client bound to the ASGI app with the DB override applied."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
