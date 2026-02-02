"""Integration tests for leads CRUD flow with real database."""

import pytest
from sqlalchemy import select

from app.core.security import create_access_token
from app.models import Lead
from tests.factories import create_lead, create_user, create_workspace, create_workspace_user


class TestLeadsAPI:
    """Tests for leads API endpoints."""

    @pytest.fixture
    async def auth_setup(self, db_session):
        """Set up authenticated user with workspace."""
        # Create user
        user = await create_user(db_session, email="test@example.com", is_superuser=True)

        # Create workspace
        workspace = await create_workspace(db_session, name="Test Workspace", slug="test-ws")

        # Link user to workspace
        await create_workspace_user(db_session, user=user, workspace=workspace, role="admin")

        await db_session.commit()

        # Create access token
        token = create_access_token(subject=user.id)

        return {
            "user": user,
            "workspace": workspace,
            "token": token,
            "headers": {
                "Authorization": f"Bearer {token}",
                "X-Workspace-Id": str(workspace.id),
            },
        }

    @pytest.mark.asyncio
    async def test_create_lead(self, client, auth_setup):
        """Should create a lead via API."""
        response = await client.post(
            "/v1/leads",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "domain": "example.com",
                "company": "Example Corp",
            },
            headers=auth_setup["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["first_name"] == "John"
        assert data["data"]["last_name"] == "Doe"
        assert data["data"]["domain"] == "example.com"
        assert data["data"]["verification_status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_leads(self, client, db_session, auth_setup):
        """Should list leads for workspace."""
        workspace = auth_setup["workspace"]

        # Create some leads
        await create_lead(
            db_session,
            workspace=workspace,
            first_name="Alice",
            last_name="Smith",
            domain="alice.com",
        )
        await create_lead(
            db_session,
            workspace=workspace,
            first_name="Bob",
            last_name="Jones",
            domain="bob.com",
        )
        await db_session.commit()

        response = await client.get(
            "/v1/leads",
            headers=auth_setup["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data["data"]
        assert len(data["data"]["items"]) >= 2

    @pytest.mark.asyncio
    async def test_get_lead_by_id(self, client, db_session, auth_setup):
        """Should get single lead by ID."""
        workspace = auth_setup["workspace"]

        lead = await create_lead(
            db_session,
            workspace=workspace,
            first_name="Charlie",
            last_name="Brown",
            domain="charlie.com",
        )
        await db_session.commit()

        response = await client.get(
            f"/v1/leads/{lead.id}",
            headers=auth_setup["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["first_name"] == "Charlie"
        assert data["data"]["id"] == lead.id

    @pytest.mark.asyncio
    async def test_update_lead(self, client, db_session, auth_setup):
        """Should update lead fields via PATCH."""
        workspace = auth_setup["workspace"]

        lead = await create_lead(
            db_session,
            workspace=workspace,
            first_name="Original",
            last_name="Name",
            domain="original.com",
        )
        await db_session.commit()

        response = await client.patch(
            f"/v1/leads/{lead.id}",
            json={
                "first_name": "Updated",
                "last_name": "Person",
            },
            headers=auth_setup["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["first_name"] == "Updated"
        assert data["data"]["last_name"] == "Person"
        assert data["data"]["domain"] == "original.com"  # Unchanged

    @pytest.mark.asyncio
    async def test_bulk_upsert_leads(self, client, auth_setup):
        """Should create multiple leads via bulk endpoint."""
        response = await client.post(
            "/v1/leads/bulk",
            json={
                "leads": [
                    {"first_name": "Bulk1", "last_name": "BulkTest", "domain": "bulk1.com"},
                    {"first_name": "Bulk2", "last_name": "BulkTest", "domain": "bulk2.com"},
                    {"first_name": "Bulk3", "last_name": "BulkTest", "domain": "bulk3.com"},
                ]
            },
            headers=auth_setup["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        # Check that leads were processed (created or updated)
        assert "created" in data["data"] or "total" in data["data"]
        # At least some leads should be created
        assert data["data"].get("created", 0) + data["data"].get("updated", 0) >= 1

    @pytest.mark.asyncio
    async def test_leads_isolation_between_workspaces(self, client, db_session, auth_setup):
        """Leads should be isolated between workspaces."""
        workspace1 = auth_setup["workspace"]

        # Create another workspace
        workspace2 = await create_workspace(db_session, name="Other Workspace", slug="other-ws")

        # Create lead in workspace1
        await create_lead(db_session, workspace=workspace1, first_name="Lead1")

        # Create lead in workspace2
        await create_lead(db_session, workspace=workspace2, first_name="Lead2")

        await db_session.commit()

        # List leads for workspace1
        response = await client.get(
            "/v1/leads",
            headers=auth_setup["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        lead_names = [lead["first_name"] for lead in data["data"]["items"]]

        assert "Lead1" in lead_names
        assert "Lead2" not in lead_names  # Should not see leads from other workspace


class TestLeadsDatabase:
    """Tests for lead operations directly on database."""

    @pytest.mark.asyncio
    async def test_lead_created_in_db(self, db_session):
        """Should persist lead to database."""
        workspace = await create_workspace(db_session)
        await create_lead(
            db_session,
            workspace=workspace,
            first_name="Database",
            last_name="Test",
        )
        await db_session.commit()

        # Query back
        result = await db_session.execute(select(Lead).where(Lead.first_name == "Database"))
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.last_name == "Test"
        assert found.workspace_id == workspace.id

    @pytest.mark.asyncio
    async def test_lead_default_values(self, db_session):
        """Should have correct default values."""
        workspace = await create_workspace(db_session)
        lead = await create_lead(db_session, workspace=workspace)
        await db_session.commit()

        assert lead.verification_status == "pending"
        assert lead.confidence_score == 0
        assert lead.mx_found is False
        assert lead.catch_all is False
        assert lead.opt_out is False
        assert lead.sales_status == "New"
