"""Password hashing + token creation/verification.

Two different token types, deliberately:
- ACCESS token: a JWT — self-contained, verified by signature alone (no DB
  lookup on every request). Short-lived (15 min) so a stolen one expires fast.
- REFRESH token: an opaque random string, stored (hashed) in the DB. Long-lived
  but *revocable* — logout or rotation kills it server-side, which a pure JWT
  can't do. This access/refresh split is the industry-standard trade-off
  between performance and revocability.
"""
import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

_hasher = PasswordHasher()  # argon2id — current OWASP recommendation


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """Returns the payload if the token is valid and unexpired, else None."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    return payload if payload.get("type") == "access" else None


def generate_refresh_token() -> tuple[str, str, datetime]:
    """Returns (raw_token_for_client, sha256_hash_for_db, expiry)."""
    raw = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    expires_at = datetime.now(UTC) + timedelta(days=get_settings().refresh_token_days)
    return raw, token_hash, expires_at


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
