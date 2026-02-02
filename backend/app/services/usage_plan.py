"""Usage and plan limits."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Usage, Workspace
from app.models.plan import PLAN_PRO, PLAN_TEAM


def get_plan_limits(plan: str) -> tuple[int, int]:
    """Returns (verifications_per_month, max_api_keys)."""
    if plan == PLAN_TEAM:
        return (settings.plan_team_verifications_per_month, settings.plan_team_api_keys)
    if plan == PLAN_PRO:
        return (settings.plan_pro_verifications_per_month, settings.plan_pro_api_keys)
    return (settings.plan_free_verifications_per_month, settings.plan_free_api_keys)


def get_rate_limit_for_plan(plan: str) -> int:
    """Requests per minute per API key."""
    limits = {"free": 30, "pro": 60, "team": 120}
    return limits.get(plan, 30)


async def get_current_usage(db: AsyncSession, workspace_id: int) -> tuple[int, int]:
    """Returns (verifications_count, exports_count) for current month."""
    now = datetime.now(UTC)
    period = now.strftime("%Y-%m")
    result = await db.execute(
        select(Usage).where(Usage.workspace_id == workspace_id, Usage.period == period)
    )
    row = result.unique().scalars().one_or_none()
    if not row:
        return (0, 0)
    return (row.verifications_count, row.exports_count)


async def increment_verification_usage(db: AsyncSession, workspace_id: int) -> int:
    """Increment verification count for current month; return new total."""
    now = datetime.now(UTC)
    period = now.strftime("%Y-%m")
    result = await db.execute(
        select(Usage).where(Usage.workspace_id == workspace_id, Usage.period == period)
    )
    row = result.unique().scalars().one_or_none()
    if not row:
        row = Usage(workspace_id=workspace_id, period=period, verifications_count=1, exports_count=0)
        db.add(row)
    else:
        row.verifications_count += 1
        row.updated_at = now
    await db.flush()
    return row.verifications_count


async def increment_export_usage(db: AsyncSession, workspace_id: int) -> int:
    now = datetime.now(UTC)
    period = now.strftime("%Y-%m")
    result = await db.execute(
        select(Usage).where(Usage.workspace_id == workspace_id, Usage.period == period)
    )
    row = result.unique().scalars().one_or_none()
    if not row:
        row = Usage(workspace_id=workspace_id, period=period, verifications_count=0, exports_count=1)
        db.add(row)
    else:
        row.exports_count += 1
        row.updated_at = now
    await db.flush()
    return row.exports_count


async def check_verification_quota(db: AsyncSession, workspace: Workspace) -> str | None:
    """Returns error message if over quota, else None."""
    verifications, _ = await get_current_usage(db, workspace.id)
    limit, _ = get_plan_limits(workspace.plan)
    if verifications >= limit:
        return f"Verification quota exceeded ({verifications}/{limit} this month)"
    return None
