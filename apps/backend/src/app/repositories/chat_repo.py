import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import Conversation, Message


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(
        self, user_id: uuid.UUID, title: str = "New chat"
    ) -> Conversation:
        conv = Conversation(user_id=user_id, title=title)
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def get_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Conversation | None:
        """Scoped by user_id — ownership is part of the QUERY, so another
        user's conversation is indistinguishable from a nonexistent one (404,
        not 403: we don't even confirm it exists)."""
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_conversations(self, user_id: uuid.UUID) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id, Conversation.is_deleted.is_(False))
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_messages(self, conversation_id: uuid.UUID) -> list[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .options(selectinload(Message.citations))
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())

    async def add_message(self, message: Message) -> Message:
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_message_with_citations(self, message_id: uuid.UUID) -> Message | None:
        """Async SQLAlchemy lesson: refresh() after commit EXPIRES relationships,
        and lazily loading them later (e.g. during response serialization)
        happens outside the async context → MissingGreenlet crash. The cure is
        explicit eager loading: fetch the row WITH its citations in one query."""
        result = await self.db.execute(
            select(Message)
            .where(Message.id == message_id)
            .options(selectinload(Message.citations))
        )
        return result.scalar_one_or_none()

    async def commit(self) -> None:
        await self.db.commit()
