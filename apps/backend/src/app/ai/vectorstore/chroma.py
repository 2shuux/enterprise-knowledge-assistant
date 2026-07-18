"""ChromaDB adapter (HTTP client → the chroma container from docker-compose).

The chroma client is synchronous, so every call is pushed off the event loop
with asyncio.to_thread — an async web server must NEVER block its loop on
network I/O, or every concurrent request stalls behind it.
"""
import asyncio

import chromadb

from app.core.logging import get_logger

from .base import VectorHit, VectorRecord

log = get_logger("vectorstore.chroma")

COLLECTION = "documents"


class ChromaVectorStore:
    def __init__(self, host: str, port: int):
        self._client = chromadb.HttpClient(host=host, port=port)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION,
            metadata={"hnsw:space": "cosine"},  # cosine distance suits text embeddings
        )

    async def upsert(self, records: list[VectorRecord]) -> None:
        if not records:
            return
        await asyncio.to_thread(
            self._collection.upsert,
            ids=[r.id for r in records],
            embeddings=[r.embedding for r in records],
            documents=[r.text for r in records],
            metadatas=[r.metadata for r in records],
        )
        log.info("vectors_upserted", count=len(records))

    async def query(self, embedding: list[float], k: int) -> list[VectorHit]:
        result = await asyncio.to_thread(
            self._collection.query, query_embeddings=[embedding], n_results=k
        )
        hits: list[VectorHit] = []
        for id_, distance, meta in zip(
            result["ids"][0], result["distances"][0], result["metadatas"][0], strict=True
        ):
            hits.append(VectorHit(id=id_, score=1.0 - distance, metadata=meta or {}))
        return hits

    async def delete_by_document(self, document_id: str) -> None:
        await asyncio.to_thread(self._collection.delete, where={"document_id": document_id})
        log.info("vectors_deleted", document_id=document_id)
