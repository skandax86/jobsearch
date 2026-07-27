"""Shared pytest fixtures for API tests."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from careerpilot.db.session import engine
from careerpilot.main import app


@pytest.fixture(autouse=True)
async def _dispose_engine():
    """Avoid asyncpg connections sticking to a closed event loop between tests."""
    yield
    await engine.dispose()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@example.com"
