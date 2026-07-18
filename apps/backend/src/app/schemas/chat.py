import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class CitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID | None
    document_name: str
    page_number: int
    excerpt: str
    relevance_score: float
    rank: int


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    confidence: float | None
    latency_ms: int | None
    created_at: datetime
    citations: list[CitationOut] = []


class AskRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New chat", max_length=255)
