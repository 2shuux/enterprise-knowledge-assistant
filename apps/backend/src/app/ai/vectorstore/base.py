"""VectorStore contract — same swappability story as EmbeddingProvider.
Chroma today; Pinecone tomorrow would be one new adapter class."""
from dataclasses import dataclass
from typing import Protocol


@dataclass
class VectorRecord:
    id: str
    embedding: list[float]
    text: str
    metadata: dict


@dataclass
class VectorHit:
    id: str
    score: float  # cosine similarity, 1.0 = identical
    metadata: dict


class VectorStore(Protocol):
    async def upsert(self, records: list[VectorRecord]) -> None: ...
    async def query(self, embedding: list[float], k: int) -> list[VectorHit]: ...
    async def delete_by_document(self, document_id: str) -> None: ...
