"""FastAPI dependencies — reusable, declarative guards.

`user: CurrentUser` in a route signature means "401 unless a valid access
token identifies an active user". `user: AdminUser` additionally means
"403 unless that user is an ADMIN". Authorization becomes part of the
route's *signature*, impossible to forget.
"""
import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.models.user import ROLE_ADMIN, User

_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise UnauthorizedError("Missing authentication token")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError("Invalid or expired token")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_admin(user: CurrentUser) -> User:
    if user.role != ROLE_ADMIN:
        raise ForbiddenError("Admin privileges required")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
