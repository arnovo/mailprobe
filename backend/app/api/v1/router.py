"""API v1 router aggregation."""
from fastapi import APIRouter

from app.api.v1 import api_keys, auth, config, exports, jobs, leads, optout, usage, verify, webhooks, workspaces

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(verify.router, prefix="/verify", tags=["verify"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
# POST /v1/leads/{id}/verify is in leads.py
api_router.include_router(optout.router, prefix="/optout", tags=["optout"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(usage.router, prefix="/usage", tags=["usage"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
