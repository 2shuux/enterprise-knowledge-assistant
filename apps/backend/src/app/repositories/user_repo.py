"""Data access for User + RefreshToken. No business logic lives here —
repositories answer 'get/save' questions, services decide what to do."""
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import RefreshToken, User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(User))
        return result.scalar_one()

    async def add(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def touch_last_login(self, user: User) -> None:
        user.last_login_at = datetime.now(UTC)
        await self.db.commit()


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, token: RefreshToken) -> None:
        self.db.add(token)
        await self.db.commit()

    async def get_active_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(UTC),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(UTC)
        await self.db.commit()
