"""FastAPI application."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="""
## Mailprobe API

B2B email finder and verifier API. Multi-tenant, ready for n8n integration.

### Features
- **Lead Management**: Create, update, and manage B2B leads
- **Email Verification**: Find and verify email addresses using MX/SMTP probes
- **Async Jobs**: Background processing with status tracking
- **Webhooks**: Real-time notifications for events
- **API Keys**: Secure access for integrations

### Authentication
- **Bearer Token**: Use `/v1/auth/login` to get access token
- **API Key**: Use `X-API-Key` header for integrations (recommended for n8n)

### Response Format
All responses follow: `{ "data": ..., "error": null }` on success,
`{ "data": null, "error": { "code": "...", "message": "..." } }` on error.
""",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "auth", "description": "Authentication: login, register, refresh token"},
        {"name": "workspaces", "description": "Workspace management"},
        {"name": "config", "description": "Workspace configuration: timeouts, patterns, web search"},
        {"name": "leads", "description": "Lead CRUD and verification"},
        {"name": "verify", "description": "Stateless email verification (without saving lead)"},
        {"name": "jobs", "description": "Background job status and logs"},
        {"name": "optout", "description": "Opt-out / unsubscribe management (GDPR)"},
        {"name": "exports", "description": "CSV export of leads"},
        {"name": "webhooks", "description": "Webhook registration and testing"},
        {"name": "usage", "description": "Usage statistics and quotas"},
        {"name": "api-keys", "description": "API key management for integrations"},
    ],
)

# CORS: incluir localhost 3001 (prod) y 3002 (dev) por si env no se parsea
_origins = list(settings.cors_origins)
for origin in ["http://localhost:3001", "http://localhost:3002", "http://127.0.0.1:3001", "http://127.0.0.1:3002"]:
    if origin not in _origins:
        _origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Consistent error response for n8n/automations."""
    return JSONResponse(
        status_code=500,
        content={
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc) if settings.debug else "Internal server error",
                "details": {},
            },
        },
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health():
    return {"status": "ok"}
