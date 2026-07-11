from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, future=True)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models (populated in later PRs)."""


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async DB session."""
    async with async_session_factory() as session:
        yield session


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """FastAPI dependency returning the session *factory*.

    Streaming endpoints (the coach SSE reply) outlive the request-scoped
    :func:`get_session` — that session is closed once the handler returns the
    streaming response. They open their own short-lived session from this factory
    inside the generator instead. Overridable in tests so the stream persists to
    the test database, same as :func:`get_session`.
    """
    return async_session_factory
