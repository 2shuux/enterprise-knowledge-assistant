"""Auth endpoints — thin HTTP layer over AuthService."""
from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: DbSession):
    return await AuthService(db).register(data)


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: DbSession):
    user, pair = await AuthService(db).login(data.email, data.password)
    return LoginResponse(**pair.model_dump(), user=UserOut.model_validate(user))


@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshRequest, db: DbSession):
    return await AuthService(db).refresh(data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshRequest, db: DbSession):
    await AuthService(db).logout(data.refresh_token)


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser):
    return user
