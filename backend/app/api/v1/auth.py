"""Auth: register, login, refresh, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password
from app.models import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse
from app.schemas.common import APIResponse

router = APIRouter()


class RefreshBody(BaseModel):
    refresh_token: str


@router.post("/register", response_model=APIResponse)
async def register(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    if result.unique().scalars().one_or_none():
        return APIResponse.err("EMAIL_EXISTS", "Email already registered", {"email": body.email})
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name or "",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return APIResponse.ok(
        {
            "user": UserResponse.model_validate(user).model_dump(),
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }
    )


@router.post("/login", response_model=APIResponse)
async def login(
    body: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.unique().scalars().one_or_none()
    from app.core.security import verify_password

    if not user or not verify_password(body.password, user.hashed_password):
        return APIResponse.err("INVALID_CREDENTIALS", "Invalid email or password")
    if not user.is_active:
        return APIResponse.err("USER_DISABLED", "Account is disabled")
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return APIResponse.ok(
        {
            "user": UserResponse.model_validate(user).model_dump(),
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }
    )


@router.post("/refresh", response_model=APIResponse)
async def refresh(
    body: RefreshBody,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        return APIResponse.err("INVALID_TOKEN", "Invalid or expired refresh token")
    sub = payload.get("sub")
    if not sub:
        return APIResponse.err("INVALID_TOKEN", "Invalid refresh token")
    result = await db.execute(select(User).where(User.id == int(sub), User.is_active.is_(True)))
    user = result.unique().scalars().one_or_none()
    if not user:
        return APIResponse.err("USER_NOT_FOUND", "User not found")
    access = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)
    return APIResponse.ok(
        {
            "access_token": access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }
    )


@router.get("/me", response_model=APIResponse)
async def me(
    current_user: User = Depends(get_current_user),
) -> APIResponse:
    return APIResponse.ok(UserResponse.model_validate(current_user).model_dump())
