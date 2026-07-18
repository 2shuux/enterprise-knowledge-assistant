"""Async database engine + session dependency.

One engine per process (lazily created & cached). Each request gets its own
AsyncSession via the `get_db` dependency — FastAPI opens it at the start of a
request and closes it at the end, so routes/services never manage connections.
"""
from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


@lru_cache
def get_engine():
    url = get_settings().database_url
    kwargs: dict = {}
    if url.startswith("sqlite"):
        # Tests use SQLite: a single shared connection keeps the in-process
        # database visible across sessions.
        kwargs = {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
    return create_async_engine(url, **kwargs)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False → ORM objects stay usable after commit,
    # which we rely on when returning freshly created rows from services.
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with get_sessionmaker()() as session:
        yield session
