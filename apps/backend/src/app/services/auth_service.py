"""All authentication business logic in one place.

Routes stay thin; this service is where the decisions live — which also
makes it the natural unit-testing target.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import ROLE_ADMIN, ROLE_USER, RefreshToken, User
from app.repositories.user_repo import RefreshTokenRepository, UserRepository
from app.schemas.auth import RegisterRequest, TokenPair


class EmailAlreadyRegisteredError(UnauthorizedError):
    status_code = 409
    code = "EMAIL_TAKEN"


class AuthService:
    def __init__(self, db: AsyncSession):
        self.users = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)

    async def register(self, data: RegisterRequest) -> User:
        if await self.users.get_by_email(data.email):
            raise EmailAlreadyRegisteredError("An account with this email already exists")

        # Bootstrap: the very first account becomes ADMIN (configurable).
        is_first = await self.users.count() == 0
        role = ROLE_ADMIN if (is_first and get_settings().first_user_is_admin) else ROLE_USER

        user = User(
            email=str(data.email).lower(),
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=role,
        )
        return await self.users.add(user)

    async def login(self, email: str, password: str) -> tuple[User, TokenPair]:
        user = await self.users.get_by_email(email)
        # Same error for "no such user" and "wrong password" — never help
        # an attacker enumerate which emails have accounts.
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("This account has been deactivated")

        await self.users.touch_last_login(user)
        return user, await self._issue_pair(user)

    async def refresh(self, raw_refresh_token: str) -> TokenPair:
        """Rotation: every refresh consumes the old token and issues a new one.
        A stolen refresh token therefore works at most once."""
        stored = await self.tokens.get_active_by_hash(hash_refresh_token(raw_refresh_token))
        if not stored:
            raise UnauthorizedError("Invalid or expired refresh token")

        user = await self.users.get_by_id(stored.user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("Invalid or expired refresh token")

        await self.tokens.revoke(stored)
        return await self._issue_pair(user)

    async def logout(self, raw_refresh_token: str) -> None:
        stored = await self.tokens.get_active_by_hash(hash_refresh_token(raw_refresh_token))
        if stored:
            await self.tokens.revoke(stored)

    async def _issue_pair(self, user: User) -> TokenPair:
        raw, token_hash, expires_at = generate_refresh_token()
        await self.tokens.add(
            RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        )
        return TokenPair(
            access_token=create_access_token(user.id, user.role),
            refresh_token=raw,
        )
