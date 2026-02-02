"""Webhook schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class WebhookCreate(BaseModel):
    url: HttpUrl
    events: list[str] = Field(..., min_length=1)  # lead.created, verification.completed, ...

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[str]) -> list[str]:
        """Validate event names."""
        valid_events = {"lead.created", "verification.completed", "export.completed", "optout.recorded"}
        for event in v:
            if event not in valid_events:
                pass  # Allow unknown events for forward compatibility
        return v


class WebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    events: list[str]
    is_active: bool
    created_at: str
