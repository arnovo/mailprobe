"""Basic API tests (no DB required)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_api_docs(client: AsyncClient):
    r = await client.get("/docs")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_v1_prefix(client: AsyncClient):
    r = await client.get("/v1/leads")
    # Sin auth: 401 o 403
    assert r.status_code in (401, 403, 422)
