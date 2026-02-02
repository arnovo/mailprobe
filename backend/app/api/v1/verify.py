"""Verify: stateless verify (name + domain -> candidates + best)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_workspace_required, require_scope
from app.schemas.common import APIResponse
from app.schemas.verify import VerifyCandidate, VerifyStatelessRequest, VerifyStatelessResponse
from app.services.usage_plan import check_verification_quota
from app.services.verifier import verify_and_pick_best

router = APIRouter()


@router.post("", response_model=APIResponse, dependencies=[require_scope("verify:run")])
async def verify_stateless(
    body: VerifyStatelessRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    workspace_required: tuple = Depends(get_workspace_required),
) -> APIResponse:
    """Stateless: first_name + last_name + domain -> candidates + best."""
    workspace, _, _ = workspace_required
    quota_err = await check_verification_quota(db, workspace)
    if quota_err:
        return APIResponse.err("QUOTA_EXCEEDED", quota_err, {"code": "quota_exceeded"})
    candidates, best_email, best_result, _ = verify_and_pick_best(
        body.first_name, body.last_name, body.domain
    )
    from app.services.usage_plan import increment_verification_usage
    await increment_verification_usage(db, workspace.id)
    best_candidate = None
    if best_result:
        best_candidate = VerifyCandidate(
            email=best_result.email,
            status=best_result.status,
            confidence_score=best_result.confidence_score,
            web_mentioned=getattr(best_result, "web_mentioned", False),
        )
    return APIResponse.ok(VerifyStatelessResponse(
        candidates=candidates,
        best=best_email or None,
        best_result=best_candidate,
    ).model_dump())

