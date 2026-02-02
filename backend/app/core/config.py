"""Application configuration."""

from __future__ import annotations

import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings from env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "Mailprobe API"
    debug: bool = False
    api_v1_prefix: str = "/v1"

    # Database
    database_url: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/mailprobe")
    database_url_sync: str = Field(default="postgresql://postgres:postgres@localhost:5432/mailprobe")

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"

    # JWT
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS: env como JSON ["http://localhost:3001","http://localhost:3002"] o string separado por comas
    cors_origins: str | list[str] = Field(
        default='["http://localhost:3001","http://localhost:3000","http://localhost:3002","http://127.0.0.1:3002"]',
        description="JSON array o comma-separated",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return [
                    "http://localhost:3001",
                    "http://localhost:3000",
                    "http://localhost:3002",
                    "http://127.0.0.1:3002",
                ]
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return [s.strip() for s in v.split(",") if s.strip()]
            return [s.strip() for s in v.split(",") if s.strip()]
        return ["http://localhost:3001", "http://localhost:3000", "http://localhost:3002", "http://127.0.0.1:3002"]

    # Rate limits (per minute)
    rate_limit_per_key: int = 60
    rate_limit_per_user: int = 30
    rate_limit_per_workspace: int = 100

    # Plans
    plan_free_verifications_per_month: int = 50
    plan_free_api_keys: int = 1
    plan_pro_verifications_per_month: int = 500
    plan_pro_api_keys: int = 5
    plan_team_verifications_per_month: int = 2000
    plan_team_api_keys: int = 20

    # Retention (months)
    retention_inactive_months: int = 24

    # Webhooks
    webhook_max_retries: int = 5
    webhook_timeout_seconds: int = 30

    # Idempotency (ttl in seconds)
    idempotency_ttl_seconds: int = 86400  # 24h

    # SMTP probe (puerto 25; en muchos entornos cloud/Docker está bloqueado o limitado)
    smtp_timeout_seconds: int = 5
    smtp_mail_from: str = "noreply@mailcheck.local"
    # DNS (MX lookup): tiempo máximo de espera por consulta
    dns_timeout_seconds: float = 5.0

    # Búsqueda web: ahora se configura por workspace (Dashboard → Configuración).
    # Las variables globales ya no se usan; cada workspace define su provider y API key.


settings = Settings()
