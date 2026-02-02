"""API dependencies: auth, workspace, RBAC, rate limit, idempotency."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import (
    decode_token,
    hash_api_key,
)
from app.models import ApiKey, User, Workspace, WorkspaceUser

# --- Auth ---

Bearer = HTTPBearer(auto_error=False)
APIKeyHeaderAuth = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user_from_token(
    db: AsyncSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(Bearer),
) -> User | None:
    if not credentials or credentials.scheme != "Bearer":
        return None
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    result = await db.execute(select(User).where(User.id == int(sub), User.is_active.is_(True)))
    return result.unique().scalars().one_or_none()


async def get_current_user_from_api_key(
    db: AsyncSession,
    api_key: str | None = Depends(APIKeyHeaderAuth),
) -> User | None:
    if not api_key or "." not in api_key:
        return None
    prefix, secret = api_key.split(".", 1)
    key_hash = hash_api_key(api_key)
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_prefix == prefix,
            ApiKey.key_hash == key_hash,
            ApiKey.revoked_at.is_(None),
        )
    )
    key = result.unique().scalars().one_or_none()
    if not key:
        return None
    key.last_used_at = datetime.now(UTC)
    # API key auth: we don't have a "user" but we have workspace
    # Return None to indicate API key auth; workspace will be resolved via get_workspace_from_api_key
    return None


async def get_workspace_from_api_key(
    db: AsyncSession,
    api_key: str | None = Depends(APIKeyHeaderAuth),
) -> tuple[ApiKey, Workspace] | None:
    if not api_key or "." not in api_key:
        return None
    key_hash = hash_api_key(api_key)
    prefix = api_key.split(".", 1)[0]
    result = await db.execute(
        select(ApiKey, Workspace)
        .join(Workspace, ApiKey.workspace_id == Workspace.id)
        .where(
            ApiKey.key_prefix == prefix,
            ApiKey.key_hash == key_hash,
            ApiKey.revoked_at.is_(None),
        )
    )
    row = result.unique().first()
    if not row:
        return None
    key, workspace = row
    key.last_used_at = datetime.now(UTC)
    return (key, workspace)


async def get_workspace_for_user(
    db: AsyncSession,
    user: User,
    workspace_id: int | None = None,
    workspace_slug: str | None = None,
) -> WorkspaceUser | None:
    if workspace_id:
        result = await db.execute(
            select(WorkspaceUser)
            .options(selectinload(WorkspaceUser.workspace))
            .where(
                WorkspaceUser.workspace_id == workspace_id,
                WorkspaceUser.user_id == user.id,
            )
        )
    elif workspace_slug:
        result = await db.execute(
            select(WorkspaceUser)
            .options(selectinload(WorkspaceUser.workspace))
            .join(Workspace, WorkspaceUser.workspace_id == Workspace.id)
            .where(Workspace.slug == workspace_slug, WorkspaceUser.user_id == user.id)
        )
    else:
        return None
    return result.unique().scalars().one_or_none()


def ensure_scope(api_key: ApiKey | None, scope: str, request: Request) -> None:
    """Call in route body: if API key auth, require scope. If Bearer auth, no-op."""
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return
    if not api_key:
        return
    scopes = [s.strip() for s in api_key.scopes.split(",") if s.strip()]
    if scope not in scopes:
        raise HTTPException(status_code=403, detail=f"Missing scope: {scope}")


def require_scope(scope: str):
    """Returns a Depends for scope check. Use dependencies=[require_scope('x')] - but ensure_scope in body is used instead to avoid AsyncSession in dep graph."""

    async def check(request: Request, workspace_required: tuple = Depends(get_workspace_required)) -> None:
        _, __, api_key = workspace_required
        ensure_scope(api_key, scope, request)

    return Depends(check)


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(Bearer),
) -> User | None:
    return await get_current_user_from_token(db, credentials)


async def get_current_user(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_superadmin():
    """Devuelve la dependencia (callable) para inyectar en Depends(require_superadmin())."""

    async def check(current_user: User = Depends(get_current_user)) -> User:
        if not is_superadmin(current_user):
            raise HTTPException(status_code=403, detail="Superadmin required")
        return current_user

    return check


def is_superadmin(user: User | None) -> bool:
    """True si el usuario es superadmin (admin@example.com o is_superuser). Para ver logs [DEBUG]."""
    if not user:
        return False
    return user.email == "admin@example.com" or getattr(user, "is_superuser", False)


def filter_log_lines_for_user(log_lines: list | None, user: User | None) -> list:
    """Quita líneas que empiezan por [DEBUG] si el usuario no es superadmin."""
    lines = log_lines or []
    if is_superadmin(user):
        return lines
    return [line for line in lines if not (line.strip().startswith("[DEBUG]"))]


async def get_workspace_id_from_header(
    x_workspace_id: int | None = Header(None, alias="X-Workspace-Id"),
    x_workspace_slug: str | None = Header(None, alias="X-Workspace-Slug"),
) -> int | None:
    """Resolve workspace from header (for UI). API key already binds to workspace."""
    return x_workspace_id  # Slug would need DB lookup in route


async def get_workspace_required(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    x_workspace_id: int | None = Header(None, alias="X-Workspace-Id"),
    x_workspace_slug: str | None = Header(None, alias="X-Workspace-Slug"),
    api_key: str | None = Depends(APIKeyHeaderAuth),
) -> tuple[Workspace, WorkspaceUser | None, ApiKey | None]:
    """
    Returns (workspace, workspace_user_or_none, api_key_or_none).
    For API key auth: workspace from key. For user auth: workspace from header.
    """
    # API key auth
    if api_key and "." in api_key:
        wk = await get_workspace_from_api_key(db, api_key)
        if wk:
            key, workspace = wk
            return (workspace, None, key)

    # User auth: need X-Workspace-Id or X-Workspace-Slug
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    wu = await get_workspace_for_user(db, current_user, workspace_id=x_workspace_id, workspace_slug=x_workspace_slug)
    if not wu:
        raise HTTPException(status_code=403, detail="Workspace not found or access denied")
    return (wu.workspace, wu, None)


def require_role(min_role: str):
    """Require at least this role (admin > member > read_only)."""

    async def check(
        workspace_required: tuple[Workspace, WorkspaceUser | None, ApiKey | None] = Depends(get_workspace_required),
    ) -> None:
        _, wu, key = workspace_required
        if key:
            # API key: has full access for its scopes; no role
            return
        if not wu:
            raise HTTPException(status_code=403, detail="Access denied")
        order = {"admin": 3, "member": 2, "read_only": 1}
        if order.get(wu.role, 0) < order.get(min_role, 0):
            raise HTTPException(status_code=403, detail="Insufficient role")

    return Depends(check)


# --- Idempotency ---


async def check_idempotency(
    workspace_id: int,
    key: str,
    db: AsyncSession,
) -> tuple[int, str] | None:
    """Returns (response_status, response_body) if idempotent hit, else None."""
    from app.models.idempotency import IdempotencyKey

    result = await db.execute(
        select(IdempotencyKey).where(
            IdempotencyKey.workspace_id == workspace_id,
            IdempotencyKey.key == key,
        )
    )
    row = result.unique().scalars().one_or_none()
    if not row:
        return None
    return (row.response_status, row.response_body)


async def save_idempotency(
    db: AsyncSession,
    workspace_id: int,
    key: str,
    request_hash: str,
    response_status: int,
    response_body: str,
) -> None:
    from app.models.idempotency import IdempotencyKey

    rec = IdempotencyKey(
        workspace_id=workspace_id,
        key=key,
        request_hash=request_hash,
        response_status=response_status,
        response_body=response_body,
    )
    db.add(rec)
    await db.commit()
