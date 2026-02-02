"""Lead schemas."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LeadCompliance(BaseModel):
    source: str = Field(default="", max_length=200)
    lawful_basis: str = Field(default="legitimate_interest", max_length=50)
    purpose: str = Field(default="b2b_sales_outreach", max_length=100)
    collected_at: datetime | None = None


class LeadBase(BaseModel):
    first_name: str = Field(default="", max_length=100)
    last_name: str = Field(default="", max_length=100)
    title: str = Field(default="", max_length=200)
    company: str = Field(default="", max_length=200)
    domain: str = Field(default="", max_length=253)
    linkedin_url: str = Field(default="", max_length=500)
    tags: list[str] | None = None
    sales_status: str = Field(default="New", max_length=50)
    source: str = Field(default="", max_length=200)
    lawful_basis: str = Field(default="legitimate_interest", max_length=50)
    purpose: str = Field(default="b2b_sales_outreach", max_length=100)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Validate and normalize domain format."""
        if not v:
            return v
        v = v.lower().strip()
        # Remove protocol if present
        v = re.sub(r"^https?://", "", v)
        # Remove trailing slash
        v = v.rstrip("/")
        # Basic domain validation
        if v and not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$", v):
            pass  # Allow invalid domains, they'll fail verification
        return v

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, v: str) -> str:
        """Validate LinkedIn URL format."""
        if not v:
            return v
        v = v.strip()
        if v and not v.startswith(("http://", "https://")):
            v = "https://" + v
        return v


class LeadCreate(LeadBase):
    """Schema for creating a lead."""

    pass


class LeadUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    company: str | None = None
    domain: str | None = None
    linkedin_url: str | None = None
    tags: list[str] | None = None
    sales_status: str | None = None
    owner_user_id: int | None = None


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    owner_user_id: int | None = None
    first_name: str
    last_name: str
    title: str
    company: str
    domain: str
    linkedin_url: str
    email_best: str
    email_candidates: list[str] | None = None
    verification_status: str
    confidence_score: int
    mx_found: bool
    catch_all: bool
    smtp_check: bool
    notes: str
    web_mentioned: bool = False
    tags: list[str] | None = None
    sales_status: str
    source: str
    lawful_basis: str
    purpose: str
    collected_at: datetime | None = None
    opt_out: bool
    opt_out_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    last_job_status: str | None = None  # Estado del último job de verificación


class LeadBulkItem(BaseModel):
    first_name: str = ""
    last_name: str = ""
    title: str = ""
    company: str = ""
    domain: str = ""
    linkedin_url: str = ""
    source: str = ""
    lawful_basis: str = "legitimate_interest"
    purpose: str = "b2b_sales_outreach"


class LeadBulkRequest(BaseModel):
    leads: list[LeadBulkItem] = Field(..., max_length=100)
