"""Conversation + RAG endpoints (M3: non-streaming; SSE arrives in M4)."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.ai.embeddings.base import EmbeddingProvider
from app.ai.factory import get_embedding_provider, get_llm_provider, get_vector_store
from app.ai.llm.base import LLMProvider
from app.ai.vectorstore.base import VectorStore
from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.repositories.chat_repo import ChatRepository
from app.schemas.chat import (
    AskRequest,
    ConversationOut,
    CreateConversationRequest,
    MessageOut,
)
from app.services.rag_service import RAGService

router = APIRouter(prefix="/conversations", tags=["chat"])

Embedder = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]
Store = Annotated[VectorStore, Depends(get_vector_store)]
Llm = Annotated[LLMProvider, Depends(get_llm_provider)]


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(data: CreateConversationRequest, user: CurrentUser, db: DbSession):
    return await ChatRepository(db).create_conversation(user.id, data.title)


@router.get("", response_model=list[ConversationOut])
async def list_conversations(user: CurrentUser, db: DbSession):
    return await ChatRepository(db).list_conversations(user.id)


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(conversation_id: uuid.UUID, user: CurrentUser, db: DbSession):
    repo = ChatRepository(db)
    conv = await repo.get_conversation(conversation_id, user.id)
    if conv is None:
        raise NotFoundError("Conversation not found")
    return await repo.list_messages(conversation_id)


@router.post("/{conversation_id}/messages", response_model=MessageOut)
async def ask(
    conversation_id: uuid.UUID,
    data: AskRequest,
    user: CurrentUser,
    db: DbSession,
    embedder: Embedder,
    store: Store,
    llm: Llm,
):
    repo = ChatRepository(db)
    conv = await repo.get_conversation(conversation_id, user.id)
    if conv is None:
        raise NotFoundError("Conversation not found")
    return await RAGService(embedder, store, llm).ask(repo, conv, data.content)
