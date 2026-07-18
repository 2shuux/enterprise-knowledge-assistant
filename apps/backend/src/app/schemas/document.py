import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_name: str
    mime_type: str
    file_size_bytes: int
    status: str
    error_message: str | None
    page_count: int
    chunk_count: int
    uploaded_at: datetime
    indexed_at: datetime | None


class DocumentListOut(BaseModel):
    items: list[DocumentOut]
    total: int
