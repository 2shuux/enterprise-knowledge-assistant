"""EmbeddingProvider contract.

Services depend on this Protocol, never on a concrete vendor. Swapping
Gemini for OpenAI (or a local model) means writing one new class — nothing
else in the codebase changes. Tests inject a fake that returns canned
vectors, so the suite runs offline and free.
"""
from typing import Protocol


class EmbeddingProvider(Protocol):
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed chunks for indexing."""
        ...

    async def embed_query(self, text: str) -> list[float]:
        """Embed a search query. Some models (incl. Gemini) are trained with
        distinct task types for documents vs queries — honoring that improves
        retrieval quality measurably."""
        ...
