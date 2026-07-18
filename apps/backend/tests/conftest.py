"""Test setup.

Tests run against a throwaway SQLite file and FAKE AI providers — fast,
offline, free. The fakes are injected through FastAPI's dependency_overrides:
the exact same seam a Pinecone or OpenAI swap would use in production.
IMPORTANT: env vars are set BEFORE any app import, because settings and the
engine are cached at first use.
"""
import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_db.sqlite3"
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["UPLOAD_DIR"] = "./test_uploads"

import asyncio  # noqa: E402
import pathlib  # noqa: E402
import shutil  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.ai.factory import (  # noqa: E402
    get_embedding_provider,
    get_llm_provider,
    get_vector_store,
)
from app.ai.llm.base import Completion  # noqa: E402
from app.ai.vectorstore.base import VectorHit  # noqa: E402
from app.core.database import get_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Base  # noqa: E402


class FakeEmbeddingProvider:
    """Deterministic 8-dim vectors — no network, no API key, no cost."""

    def __init__(self):
        self.document_calls: list[list[str]] = []

    async def embed_documents(self, texts):
        self.document_calls.append(list(texts))
        return [[float(len(t) % 7) + 0.1] * 8 for t in texts]

    async def embed_query(self, text):
        return [0.5] * 8


class FakeVectorStore:
    """Records every upsert/delete so tests can assert on vector traffic."""

    def __init__(self):
        self.records: dict[str, object] = {}

    async def upsert(self, records):
        for r in records:
            self.records[r.id] = r

    async def query(self, embedding, k):
        return [
            VectorHit(id=r.id, score=0.9, text=r.text, metadata=r.metadata)
            for r in list(self.records.values())[:k]
        ]

    async def delete_by_document(self, document_id):
        self.records = {
            rid: r
            for rid, r in self.records.items()
            if r.metadata.get("document_id") != document_id
        }


class FakeLLMProvider:
    """Canned grounded answer citing chunks [1] and [2]."""

    def __init__(self):
        self.calls: list[dict] = []

    async def complete(self, system, user):
        self.calls.append({"system": system, "user": user})
        return Completion(
            text="Employees receive 20 days of leave per year [1]. "
            "Unused days may carry over [2].",
            prompt_tokens=100,
            completion_tokens=25,
        )


@pytest.fixture()
def fake_llm():
    return FakeLLMProvider()


@pytest.fixture()
def fake_embedder():
    return FakeEmbeddingProvider()


@pytest.fixture()
def fake_store():
    return FakeVectorStore()


@pytest.fixture()
def client(fake_embedder, fake_store, fake_llm):
    async def _create_all():
        async with get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create_all())
    app = create_app()
    app.dependency_overrides[get_embedding_provider] = lambda: fake_embedder
    app.dependency_overrides[get_vector_store] = lambda: fake_store
    app.dependency_overrides[get_llm_provider] = lambda: fake_llm
    with TestClient(app) as c:
        yield c


def pytest_sessionfinish(session, exitstatus):
    pathlib.Path("./test_db.sqlite3").unlink(missing_ok=True)
    shutil.rmtree("./test_uploads", ignore_errors=True)
