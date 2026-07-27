"""LinkedIn OAuth API tests (legacy connect endpoints; dashboard uses Cursor MCP)."""

from __future__ import annotations

import pytest

from careerpilot.config import settings


@pytest.mark.asyncio
async def test_linkedin_status_endpoint(client):
    response = await client.get("/api/v1/auth/linkedin/status")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "enabled" in data
    assert "mock" in data
    assert "scopes" in data
    assert "openid" in data["scopes"]


@pytest.mark.asyncio
async def test_job_discovery_agent_uses_providers(client, unique_email, monkeypatch):
    monkeypatch.setattr(settings, "linkedin_mock", True)

    register = await client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "securepass123", "display_name": "LI User"},
    )
    assert register.status_code == 201
    token = register.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    agent = await client.post(
        "/api/v1/agents/job-discovery/run",
        headers=headers,
        json={"query": "python", "include_demo": True, "include_remotive": False, "limit": 10},
    )
    assert agent.status_code == 200, agent.text
    data = agent.json()["data"]
    assert data["agent"] == "job_discovery"
    assert data["linkedin_connected"] is False
    assert data["discovered"] >= 1
    assert any(t["tool"] == "job_providers_discover" for t in data["tool_trace"])


@pytest.mark.asyncio
async def test_linkedin_connect_requires_auth(client):
    response = await client.get("/api/v1/auth/linkedin/connect", params={"redirect": "false"})
    assert response.status_code == 401
