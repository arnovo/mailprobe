"""Usage: get current usage for workspace."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_workspace_required, require_scope
from app.schemas.common import APIResponse
from app.services.usage_plan import get_current_usage, get_plan_limits

router = APIRouter()


@router.get("", response_model=APIResponse, dependencies=[require_scope("leads:read")])
async def get_usage(
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    workspace, _, _ = workspace_required
    verifications, exports = await get_current_usage(db, workspace.id)
    limit_verifications, limit_api_keys = get_plan_limits(workspace.plan)
    return APIResponse.ok(
        {
            "period": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m"),
            "verifications": verifications,
            "verifications_limit": limit_verifications,
            "exports": exports,
            "plan": workspace.plan,
        }
    )
