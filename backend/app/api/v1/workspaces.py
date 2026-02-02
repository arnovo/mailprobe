"""Workspaces: list for current user (Bearer auth)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models import User, WorkspaceUser
from app.schemas.auth import WorkspaceResponse
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("", response_model=APIResponse)
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse:
    """List workspaces for current user (Bearer only)."""
    r = await db.execute(
        select(WorkspaceUser)
        .options(selectinload(WorkspaceUser.workspace))
        .where(WorkspaceUser.user_id == current_user.id)
    )
    wus = r.unique().scalars().all()
    items = [WorkspaceResponse.model_validate(wu.workspace).model_dump() for wu in wus]
    return APIResponse.ok({"items": items})
