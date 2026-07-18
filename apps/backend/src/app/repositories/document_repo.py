import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, doc: Document) -> Document:
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def get(self, doc_id: uuid.UUID) -> Document | None:
        return await self.db.get(Document, doc_id)

    async def get_by_checksum(self, checksum: str) -> Document | None:
        result = await self.db.execute(
            select(Document).where(Document.checksum_sha256 == checksum)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> tuple[list[Document], int]:
        result = await self.db.execute(
            select(Document).order_by(Document.uploaded_at.desc())
        )
        docs = list(result.scalars().all())
        return docs, len(docs)

    async def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        self.db.add_all(chunks)
        await self.db.commit()

    async def delete_chunks(self, doc_id: uuid.UUID) -> None:
        await self.db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc_id))
        await self.db.commit()

    async def delete(self, doc: Document) -> None:
        await self.db.delete(doc)
        await self.db.commit()

    async def commit(self) -> None:
        await self.db.commit()

    async def count_chunks(self, doc_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(DocumentChunk)
            .where(DocumentChunk.document_id == doc_id)
        )
        return result.scalar_one()
