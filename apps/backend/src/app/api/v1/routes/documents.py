"""Document endpoints. Reading is for every authenticated user;
upload/delete/reindex are admin-only — enforced by the AdminUser dependency,
not by UI hiding."""
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, status

from app.ai.embeddings.base import EmbeddingProvider
from app.ai.factory import get_embedding_provider, get_vector_store
from app.ai.vectorstore.base import VectorStore
from app.core.dependencies import AdminUser, CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.repositories.document_repo import DocumentRepository
from app.schemas.document import DocumentListOut, DocumentOut
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/documents", tags=["documents"])

Embedder = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]
Store = Annotated[VectorStore, Depends(get_vector_store)]


@router.post("", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile,
    admin: AdminUser,
    db: DbSession,
    embedder: Embedder,
    store: Store,
    background: BackgroundTasks,
):
    service = IngestionService(embedder, store)
    data = await file.read()
    doc = await service.upload_document(
        DocumentRepository(db), file.filename or "unnamed", data, file.content_type or "", admin.id
    )
    # 202 Accepted: "received, working on it" — the pipeline runs after the response.
    background.add_task(service.run_pipeline, doc.id)
    return doc


@router.get("", response_model=DocumentListOut)
async def list_documents(user: CurrentUser, db: DbSession):
    docs, total = await DocumentRepository(db).list_all()
    return DocumentListOut(items=[DocumentOut.model_validate(d) for d in docs], total=total)


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(document_id: uuid.UUID, user: CurrentUser, db: DbSession):
    doc = await DocumentRepository(db).get(document_id)
    if doc is None:
        raise NotFoundError("Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID, admin: AdminUser, db: DbSession, embedder: Embedder, store: Store
):
    await IngestionService(embedder, store).delete_document(DocumentRepository(db), document_id)


@router.post(
    "/{document_id}/reindex", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED
)
async def reindex_document(
    document_id: uuid.UUID,
    admin: AdminUser,
    db: DbSession,
    embedder: Embedder,
    store: Store,
    background: BackgroundTasks,
):
    service = IngestionService(embedder, store)
    doc = await service.reindex_document(DocumentRepository(db), document_id)
    background.add_task(service.run_pipeline, doc.id)
    return doc
