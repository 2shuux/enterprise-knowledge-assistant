"""Test setup.

Tests run against a throwaway SQLite file — fast, zero external services,
works identically on your Mac and in CI. (Real-Postgres integration tests
via testcontainers are a hardening-milestone upgrade.)
IMPORTANT: env vars are set BEFORE any app import, because settings and the
engine are cached at first use.
"""
import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_db.sqlite3"
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET"] = "test-secret"

import asyncio  # noqa: E402
import pathlib  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import get_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture()
def client():
    async def _create_all():
        async with get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create_all())
    with TestClient(create_app()) as c:
        yield c


def pytest_sessionfinish(session, exitstatus):
    pathlib.Path("./test_db.sqlite3").unlink(missing_ok=True)
