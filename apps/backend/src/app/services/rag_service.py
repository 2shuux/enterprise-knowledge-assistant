"""The RAG query pipeline (Milestone 3 — non-streaming).

ask() = embed question → vector search → grounded prompt → LLM →
parse [n] markers → resolve citations → persist everything.

Design choice worth defending in an interview: citations are resolved
SERVER-SIDE against the chunks we actually retrieved. The model can only
cite [1..k]; anything else is dropped. It is structurally impossible for
a hallucinated source to render as a clickable citation.
"""
import re
import time
import uuid

from app.ai.embeddings.base import EmbeddingProvider
from app.ai.llm.base import LLMProvider
from app.ai.prompts.rag import SYSTEM_PROMPT, build_user_prompt
from app.ai.vectorstore.base import VectorHit, VectorStore
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.chat import (
    ROLE_ASSISTANT_MSG,
    ROLE_USER_MSG,
    Conversation,
    Message,
    MessageCitation,
)
from app.repositories.chat_repo import ChatRepository

log = get_logger("rag")

_CITATION_RE = re.compile(r"\[(\d+)\]")


class RAGService:
    def __init__(self, embedder: EmbeddingProvider, store: VectorStore, llm: LLMProvider):
        self.embedder = embedder
        self.store = store
        self.llm = llm
        self.settings = get_settings()

    async def ask(self, repo: ChatRepository, conversation: Conversation, question: str) -> Message:
        started = time.perf_counter()

        await repo.add_message(
            Message(conversation_id=conversation.id, role=ROLE_USER_MSG, content=question)
        )

        # 1. retrieve
        query_vector = await self.embedder.embed_query(question)
        hits = await self.store.query(query_vector, k=self.settings.retrieval_k)
        log.info("retrieved", hits=len(hits), top_score=hits[0].score if hits else None)

        # 2. generate (or short-circuit when the index is empty)
        if not hits:
            answer_text = (
                "I could not find any indexed documents to answer from. "
                "Please ask an administrator to upload relevant documents first."
            )
            completion_tokens = prompt_tokens = None
        else:
            completion = await self.llm.complete(
                system=SYSTEM_PROMPT, user=build_user_prompt(question, hits)
            )
            answer_text = completion.text
            prompt_tokens = completion.prompt_tokens
            completion_tokens = completion.completion_tokens

        # 3. resolve citations + confidence
        cited = _extract_cited_hits(answer_text, hits)
        confidence = _confidence(answer_text, cited) if hits else None

        assistant = Message(
            conversation_id=conversation.id,
            role=ROLE_ASSISTANT_MSG,
            content=answer_text,
            model=self.settings.chat_model if hits else None,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=int((time.perf_counter() - started) * 1000),
            confidence=confidence,
        )
        assistant.citations = [
            MessageCitation(
                chunk_id=_safe_uuid(h.id),
                document_id=_safe_uuid(h.metadata.get("document_id")),
                document_name=h.metadata.get("document_name", "unknown"),
                page_number=int(h.metadata.get("page_number", 0)),
                excerpt=h.text[:300],
                relevance_score=round(h.score, 4),
                rank=rank,
            )
            for rank, h in enumerate(cited, start=1)
        ]
        await repo.add_message(assistant)

        # First question titles the conversation (like ChatGPT does)
        if conversation.title == "New chat":
            conversation.title = question[:80]
            await repo.commit()

        # Re-fetch with citations eagerly loaded — see get_message_with_citations
        saved = await repo.get_message_with_citations(assistant.id)
        assert saved is not None
        return saved


def _extract_cited_hits(answer: str, hits: list[VectorHit]) -> list[VectorHit]:
    """Map [n] markers back to retrieved chunks; ignore out-of-range numbers.
    Preserves first-mention order, deduplicated."""
    seen: list[int] = []
    for match in _CITATION_RE.finditer(answer):
        n = int(match.group(1))
        if 1 <= n <= len(hits) and n not in seen:
            seen.append(n)
    return [hits[n - 1] for n in seen]


def _confidence(answer: str, cited: list[VectorHit]) -> float:
    """Documented heuristic, not a probability:
    (mean retrieval score of cited chunks) × (0.5 + 0.5 × citation coverage),
    where coverage = fraction of sentences carrying at least one [n] marker.
    Uncited answers score 0 — an answer that cites nothing deserves no trust
    in a grounded system."""
    if not cited:
        return 0.0
    mean_score = sum(h.score for h in cited) / len(cited)
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]
    covered = sum(1 for s in sentences if _CITATION_RE.search(s))
    coverage = covered / len(sentences) if sentences else 0.0
    return round(min(1.0, mean_score * (0.5 + 0.5 * coverage)), 3)


def _safe_uuid(value) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None
