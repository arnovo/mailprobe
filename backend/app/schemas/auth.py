"""Auth schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    is_active: bool


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    plan: str


class ApiKeyCreate(BaseModel):
    name: str
    scopes: list[str]  # leads:read, leads:write, verify:run, exports:run, optout:write, webhooks:write


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    key_prefix: str
    scopes: list[str]
    rate_limit_per_minute: int
    last_used_at: str | None
    created_at: str
    revoked_at: str | None


class ApiKeyCreated(ApiKeyResponse):
    """Only on create: full key shown once."""

    key: str  # ef_xxx.secret
