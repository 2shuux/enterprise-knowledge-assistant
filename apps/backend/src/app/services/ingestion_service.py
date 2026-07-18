"""Document ingestion pipeline.

upload_document() runs in the request: validate → save file → create row →
return immediately (202). The heavy work happens in run_pipeline(), executed
as a background task AFTER the response is sent — uploads feel instant and a
crash mid-pipeline can't take the request down; it lands in status=FAILED
with the error recorded for the admin to see.

Note: the background task creates ITS OWN db session — the request's session
closes when the response goes out.
"""
import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.ai.embeddings.base import EmbeddingProvider
from app.ai.ingestion.chunker import chunk_pages
from app.ai.ingestion.cleaner import clean_text
from app.ai.ingestion.parsers import PageText, sniff_and_parse
from app.ai.vectorstore.base import VectorRecord, VectorStore
from app.core.config import get_settings
from app.core.database import get_sessionmaker
from app.core.exceptions import AppError, NotFoundError
from app.core.logging import get_logger
from app.models.document import (
    STATUS_FAILED,
    STATUS_INDEXED,
    STATUS_PROCESSING,
    Document,
    DocumentChunk,
)
from app.repositories.document_repo import DocumentRepository

log = get_logger("ingestion")


class DuplicateDocumentError(AppError):
    status_code = 409
    code = "DUPLICATE_DOCUMENT"


class FileTooLargeError(AppError):
    status_code = 413
    code = "FILE_TOO_LARGE"


class IngestionService:
    def __init__(self, embedder: EmbeddingProvider, store: VectorStore):
        self.embedder = embedder
        self.store = store
        self.settings = get_settings()

    # ---------- request-time ----------

    async def upload_document(
        self, repo: DocumentRepository, filename: str, data: bytes, mime: str, owner_id: uuid.UUID
    ) -> Document:
        if len(data) > self.settings.max_upload_bytes:
            raise FileTooLargeError(
                f"File exceeds the {self.settings.max_upload_bytes // (1024*1024)} MB limit"
            )

        # Parse now (fast) so obviously-broken files fail the REQUEST with a
        # clear error instead of a mysterious FAILED status later.
        sniff_and_parse(filename, data)

        checksum = hashlib.sha256(data).hexdigest()
        if await repo.get_by_checksum(checksum):
            raise DuplicateDocumentError("This exact file has already been uploaded")

        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        doc_id = uuid.uuid4()
        ext = filename.rsplit(".", 1)[-1].lower()
        storage_path = upload_dir / f"{doc_id}.{ext}"
        storage_path.write_bytes(data)

        doc = Document(
            id=doc_id,
            original_name=filename,
            mime_type=mime or "application/octet-stream",
            file_size_bytes=len(data),
            storage_path=str(storage_path),
            status=STATUS_PROCESSING,
            checksum_sha256=checksum,
            owner_id=owner_id,
        )
        return await repo.add(doc)

    # ---------- background ----------

    async def run_pipeline(self, document_id: uuid.UUID) -> None:
        async with get_sessionmaker()() as db:
            repo = DocumentRepository(db)
            doc = await repo.get(document_id)
            if doc is None:
                return
            try:
                await self._process(repo, doc)
            except Exception as exc:  # noqa: BLE001 — any failure lands in FAILED status
                log.exception("ingestion_failed", document_id=str(document_id))
                doc.status = STATUS_FAILED
                doc.error_message = str(exc)[:2000]
                await repo.commit()

    async def _process(self, repo: DocumentRepository, doc: Document) -> None:
        log.info("ingestion_started", document_id=str(doc.id), name=doc.original_name)

        data = Path(doc.storage_path).read_bytes()
        pages = sniff_and_parse(doc.original_name, data)
        pages = [PageText(p.page_number, clean_text(p.text)) for p in pages]

        chunks = chunk_pages(
            pages, self.settings.chunk_size_chars, self.settings.chunk_overlap_chars
        )
        log.info("chunked", document_id=str(doc.id), pages=len(pages), chunks=len(chunks))

        vectors = await self.embedder.embed_documents([c.content for c in chunks])

        chunk_rows = [
            DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                content=c.content,
                token_estimate=c.token_estimate,
            )
            for c in chunks
        ]
        await repo.add_chunks(chunk_rows)

        await self.store.upsert(
            [
                VectorRecord(
                    id=str(row.id),
                    embedding=vec,
                    text=row.content,
                    metadata={
                        "document_id": str(doc.id),
                        "document_name": doc.original_name,
                        "page_number": row.page_number,
                        "chunk_index": row.chunk_index,
                    },
                )
                for row, vec in zip(chunk_rows, vectors, strict=True)
            ]
        )

        doc.page_count = len(pages)
        doc.chunk_count = len(chunk_rows)
        doc.status = STATUS_INDEXED
        doc.indexed_at = datetime.now(UTC)
        await repo.commit()
        log.info("ingestion_complete", document_id=str(doc.id), chunks=len(chunk_rows))

    # ---------- maintenance ----------

    async def delete_document(self, repo: DocumentRepository, document_id: uuid.UUID) -> None:
        doc = await repo.get(document_id)
        if doc is None:
            raise NotFoundError("Document not found")
        await self.store.delete_by_document(str(document_id))
        Path(doc.storage_path).unlink(missing_ok=True)
        await repo.delete(doc)  # chunks cascade
        log.info("document_deleted", document_id=str(document_id))

    async def reindex_document(self, repo: DocumentRepository, document_id: uuid.UUID) -> Document:
        doc = await repo.get(document_id)
        if doc is None:
            raise NotFoundError("Document not found")
        await self.store.delete_by_document(str(document_id))
        await repo.delete_chunks(document_id)
        doc.status = STATUS_PROCESSING
        doc.error_message = None
        doc.chunk_count = 0
        await repo.commit()
        return doc
