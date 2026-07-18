"""User + RefreshToken tables.

Security notes worth internalizing:
- We store a password *hash* (argon2), never the password. Hashing is one-way;
  even a full database leak doesn't reveal passwords.
- Refresh tokens are stored *hashed* too (SHA-256). If the DB leaks, the
  attacker still can't use the tokens — they only ever exist in plaintext
  on the client.
"""
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

ROLE_ADMIN = "ADMIN"
ROLE_USER = "USER"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(sa.String(255))
    full_name: Mapped[str] = mapped_column(sa.String(255))
    role: Mapped[str] = mapped_column(sa.String(20), default=ROLE_USER)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(sa.String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")
