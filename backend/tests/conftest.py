"""Pytest fixtures for integration tests.

Uses PostgreSQL (via testcontainers) if Docker is available, otherwise falls back to SQLite.
Set TEST_USE_POSTGRES=1 to force PostgreSQL (will fail if Docker is not running).
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.database import Base
from app.main import app


def _setup_docker_host() -> None:
    """Configure Docker for macOS Docker Desktop if needed."""
    # macOS Docker Desktop uses a different socket location
    macos_socket = Path.home() / ".docker" / "run" / "docker.sock"
    if macos_socket.exists():
        if not os.getenv("DOCKER_HOST"):
            os.environ["DOCKER_HOST"] = f"unix://{macos_socket}"
        # Disable Ryuk (reaper) on macOS - has issues with Docker Desktop socket mounting
        if not os.getenv("TESTCONTAINERS_RYUK_DISABLED"):
            os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"


def _docker_available() -> bool:
    """Check if Docker is available."""
    _setup_docker_host()
    try:
        import docker

        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


# Determine which database to use
USE_POSTGRES = os.getenv("TEST_USE_POSTGRES", "").lower() in ("1", "true", "yes") or _docker_available()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for test session (only if Docker available)."""
    if not USE_POSTGRES:
        yield None
        return

    _setup_docker_host()  # Ensure Docker socket is configured
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="function")
async def db_engine(postgres_container):
    """Create async engine - PostgreSQL if Docker available, else SQLite."""
    if postgres_container is not None:
        # PostgreSQL via testcontainers
        sync_url = postgres_container.get_connection_url()
        async_url = sync_url.replace("postgresql://", "postgresql+asyncpg://").replace("psycopg2", "asyncpg")
        engine = create_async_engine(async_url, echo=False)
    else:
        # SQLite fallback
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async session for tests."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden database dependency."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# Import mocks from mocks.py
pytest_plugins = ["tests.mocks"]
