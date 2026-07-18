"""Gemini embeddings via the google-genai SDK.

Free-tier friendly: batched calls + exponential-backoff retry, because
rate-limit (429) responses are EXPECTED on the free tier and must be
handled, not crashed on.
"""
import asyncio

from google import genai
from google.genai import types

from app.core.logging import get_logger

log = get_logger("embeddings.gemini")

_BATCH_SIZE = 64
_MAX_RETRIES = 4


class GeminiEmbeddingProvider:
    def __init__(self, api_key: str, model: str = "gemini-embedding-001"):
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to apps/backend/.env "
                "(get a free key at https://aistudio.google.com)"
            )
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), _BATCH_SIZE):
            batch = texts[start : start + _BATCH_SIZE]
            vectors.extend(await self._embed(batch, task_type="RETRIEVAL_DOCUMENT"))
            log.info("embedded_batch", count=len(batch), total_done=len(vectors))
        return vectors

    async def embed_query(self, text: str) -> list[float]:
        return (await self._embed([text], task_type="RETRIEVAL_QUERY"))[0]

    async def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        delay = 2.0
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = await self._client.aio.models.embed_content(
                    model=self._model,
                    contents=texts,
                    config=types.EmbedContentConfig(task_type=task_type),
                )
                return [e.values for e in response.embeddings]
            except Exception as exc:  # noqa: BLE001 — SDK raises assorted transport errors
                if attempt == _MAX_RETRIES:
                    raise
                log.warning("embed_retry", attempt=attempt, error=str(exc), sleep=delay)
                await asyncio.sleep(delay)
                delay *= 2  # exponential backoff: 2s, 4s, 8s
        raise RuntimeError("unreachable")
