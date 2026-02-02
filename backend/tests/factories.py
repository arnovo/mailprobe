"""Factory classes for test data generation using factory_boy and Faker."""

from __future__ import annotations

from datetime import UTC, datetime

import factory
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, Lead, User, Workspace, WorkspaceUser

fake = Faker()

# Pre-computed bcrypt hash for "testpass123" to avoid bcrypt/passlib compatibility issues
TEST_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qE8.qE8.qE8.qE"


# =============================================================================
# Factory Classes (following factory_boy pattern)
# =============================================================================


class UserFactory(factory.Factory):
    """Factory for User model."""

    class Meta:
        model = User

    email = factory.LazyAttribute(lambda _: fake.unique.email())
    hashed_password = TEST_PASSWORD_HASH
    full_name = factory.LazyAttribute(lambda _: fake.name())
    is_active = True
    is_superuser = False
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))


class WorkspaceFactory(factory.Factory):
    """Factory for Workspace model."""

    class Meta:
        model = Workspace

    name = factory.LazyAttribute(lambda _: fake.company())
    slug = factory.LazyAttribute(lambda _: fake.slug())
    plan = "free"
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))


class LeadFactory(factory.Factory):
    """Factory for Lead model."""

    class Meta:
        model = Lead

    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name = factory.LazyAttribute(lambda _: fake.last_name())
    domain = factory.LazyAttribute(lambda _: fake.domain_name())
    company = factory.LazyAttribute(lambda _: fake.company())
    title = factory.LazyAttribute(lambda _: fake.job())
    verification_status = "pending"
    confidence_score = 0
    mx_found = False
    catch_all = False
    smtp_check = False
    notes = ""
    web_mentioned = False
    sales_status = "New"
    source = "test"
    lawful_basis = "legitimate_interest"
    purpose = "b2b_sales_outreach"
    opt_out = False
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))


class JobFactory(factory.Factory):
    """Factory for Job model."""

    class Meta:
        model = Job

    job_id = factory.LazyAttribute(lambda _: fake.uuid4())
    job_type = "verify_lead"
    status = "pending"
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))


# =============================================================================
# Async helper functions (persist to database)
# =============================================================================


async def create_user(
    db: AsyncSession,
    *,
    email: str | None = None,
    hashed_password: str = TEST_PASSWORD_HASH,
    full_name: str | None = None,
    is_active: bool = True,
    is_superuser: bool = False,
) -> User:
    """Create and persist a User."""
    kwargs = {
        "hashed_password": hashed_password,
        "is_active": is_active,
        "is_superuser": is_superuser,
    }
    if email is not None:
        kwargs["email"] = email
    if full_name is not None:
        kwargs["full_name"] = full_name
    user = UserFactory.build(**kwargs)
    db.add(user)
    await db.flush()
    return user


async def create_workspace(
    db: AsyncSession,
    *,
    name: str | None = None,
    slug: str | None = None,
    plan: str = "free",
) -> Workspace:
    """Create and persist a Workspace."""
    kwargs = {"plan": plan}
    if name is not None:
        kwargs["name"] = name
    if slug is not None:
        kwargs["slug"] = slug
    workspace = WorkspaceFactory.build(**kwargs)
    db.add(workspace)
    await db.flush()
    return workspace


async def create_workspace_user(
    db: AsyncSession,
    *,
    user: User | None = None,
    workspace: Workspace | None = None,
    role: str = "member",
) -> WorkspaceUser:
    """Create and persist a WorkspaceUser link."""
    if user is None:
        user = await create_user(db)
    if workspace is None:
        workspace = await create_workspace(db)

    wu = WorkspaceUser(
        user_id=user.id,
        workspace_id=workspace.id,
        role=role,
        created_at=datetime.now(UTC),
    )
    db.add(wu)
    await db.flush()
    return wu


async def create_lead(
    db: AsyncSession,
    *,
    workspace: Workspace | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    domain: str | None = None,
    company: str | None = None,
    title: str | None = None,
    verification_status: str = "pending",
    **extra_kwargs,
) -> Lead:
    """Create and persist a Lead."""
    if workspace is None:
        workspace = await create_workspace(db)

    kwargs = {
        "workspace_id": workspace.id,
        "verification_status": verification_status,
        **extra_kwargs,
    }
    if first_name is not None:
        kwargs["first_name"] = first_name
    if last_name is not None:
        kwargs["last_name"] = last_name
    if domain is not None:
        kwargs["domain"] = domain
    if company is not None:
        kwargs["company"] = company
    if title is not None:
        kwargs["title"] = title

    lead = LeadFactory.build(**kwargs)
    db.add(lead)
    await db.flush()
    return lead


async def create_job(
    db: AsyncSession,
    *,
    workspace: Workspace | None = None,
    job_id: str | None = None,
    job_type: str = "verify_lead",
    status: str = "pending",
    **extra_kwargs,
) -> Job:
    """Create and persist a Job."""
    if workspace is None:
        workspace = await create_workspace(db)

    kwargs = {
        "workspace_id": workspace.id,
        "job_type": job_type,
        "status": status,
        **extra_kwargs,
    }
    if job_id is not None:
        kwargs["job_id"] = job_id

    job = JobFactory.build(**kwargs)
    db.add(job)
    await db.flush()
    return job
