"""Document + DocumentChunk tables.

A Document is the uploaded file; DocumentChunks are the retrieval units the
AI actually searches over. Chunk rows hold the TEXT + metadata (page number,
position); the VECTOR for each chunk lives in ChromaDB under the same id.
Postgres stays the source of truth — vectors are always rebuildable from it.
"""
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

STATUS_PROCESSING = "PROCESSING"
STATUS_INDEXED = "INDEXED"
STATUS_FAILED = "FAILED"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    original_name: Mapped[str] = mapped_column(sa.String(512))
    mime_type: Mapped[str] = mapped_column(sa.String(100))
    file_size_bytes: Mapped[int] = mapped_column(sa.BigInteger)
    storage_path: Mapped[str] = mapped_column(sa.String(1024))
    status: Mapped[str] = mapped_column(sa.String(20), default=STATUS_PROCESSING)
    error_message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    page_count: Mapped[int] = mapped_column(default=0)
    chunk_count: Mapped[int] = mapped_column(default=0)
    checksum_sha256: Mapped[str] = mapped_column(sa.String(64), unique=True)  # blocks duplicates
    owner_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, sa.ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    indexed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    # This id is ALSO the vector id in ChromaDB — one join resolves any
    # retrieval hit back to its document and page. No dual-write drift.
    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column()
    page_number: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(sa.Text)
    token_estimate: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )

    document: Mapped[Document] = relationship(back_populates="chunks")
