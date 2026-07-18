"""Auth DTOs — the API's public contract.

ORM models NEVER cross the API boundary; these Pydantic schemas do.
That separation lets the DB schema evolve without breaking clients,
and guarantees fields like password_hash can never leak into a response.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # lets us build from ORM objects

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(TokenPair):
    user: UserOut
