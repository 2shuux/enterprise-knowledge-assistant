"""Builds AI adapters from settings — the ONLY place that knows which
vendor is configured. FastAPI routes receive these via Depends, which is
also the seam where tests inject fakes (dependency_overrides)."""
from functools import lru_cache

from app.ai.embeddings.base import EmbeddingProvider
from app.ai.embeddings.gemini import GeminiEmbeddingProvider
from app.ai.vectorstore.base import VectorStore
from app.ai.vectorstore.chroma import ChromaVectorStore
from app.core.config import get_settings


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    return GeminiEmbeddingProvider(
        api_key=settings.gemini_api_key, model=settings.embedding_model
    )


@lru_cache
def get_vector_store() -> VectorStore:
    settings = get_settings()
    return ChromaVectorStore(host=settings.chroma_host, port=settings.chroma_port)
