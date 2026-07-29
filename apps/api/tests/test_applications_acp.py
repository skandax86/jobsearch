"""Tests for applications tracker API and ACP workflow registration."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from careerpilot.acp.orchestrator import acp
from careerpilot.mcp.storage.server import call_storage_tool, storage_mcp


async def _auth_headers(client, unique_email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "securepass123", "display_name": "Seeker"},
    )
    assert response.status_code == 201, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_acp_core_workflows_registered():
    import careerpilot.acp.workflows  # noqa: F401

    registered = set(acp.list_workflows())
    assert {"resume_parse", "job_discovery", "tailor_resume"} <= registered


def test_storage_mcp_lists_tools():
    names = {t["name"] for t in storage_mcp.list_tools()}
    assert names == {"put_object", "get_object"}


@pytest.mark.asyncio
async def test_storage_mcp_put_get_roundtrip(monkeypatch):
    store: dict[str, bytes] = {}

    async def fake_put(*, object_key: str, data: bytes, content_type: str) -> None:
        _ = content_type
        store[object_key] = data

    async def fake_get(object_key: str) -> bytes:
        return store[object_key]

    monkeypatch.setattr("careerpilot.mcp.storage.server.object_storage.put_object", fake_put)
    monkeypatch.setattr("careerpilot.mcp.storage.server.object_storage.get_object", fake_get)

    import base64

    payload = b"hello-resume"
    put = await call_storage_tool(
        "put_object",
        object_key="users/test/source.pdf",
        data_b64=base64.b64encode(payload).decode("ascii"),
        content_type="application/pdf",
    )
    assert put.status == "SUCCESS"
    got = await call_storage_tool("get_object", object_key="users/test/source.pdf")
    assert got.status == "SUCCESS"
    assert base64.b64decode((got.result or {})["data_b64"]) == payload


@pytest.mark.asyncio
async def test_applications_tracker_crud(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    discover = await client.post(
        "/api/v1/jobs/discover",
        headers=headers,
        json={"query": "python", "include_demo": True, "include_remotive": False, "limit": 5},
    )
    assert discover.status_code == 200, discover.text
    job_id = discover.json()["data"]["items"][0]["id"]

    created = await client.post(
        "/api/v1/applications",
        headers=headers,
        json={"job_posting_id": job_id, "status": "interested"},
    )
    assert created.status_code == 201, created.text
    app = created.json()["data"]
    assert app["job_posting_id"] == job_id
    assert app["status"] == "interested"
    application_id = app["id"]

    listed = await client.get("/api/v1/applications", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] >= 1

    patched = await client.patch(
        f"/api/v1/applications/{application_id}",
        headers=headers,
        json={"status": "applied"},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["data"]["status"] == "applied"

    deleted = await client.delete(f"/api/v1/applications/{application_id}", headers=headers)
    assert deleted.status_code == 200
    listed_after = await client.get("/api/v1/applications", headers=headers)
    ids = {item["id"] for item in listed_after.json()["data"]["items"]}
    assert application_id not in ids


@pytest.mark.asyncio
async def test_acp_workflows_list_endpoint(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    response = await client.get("/api/v1/agents/acp/workflows", headers=headers)
    assert response.status_code == 200
    workflows = set(response.json()["data"]["workflows"])
    assert {"resume_parse", "job_discovery", "tailor_resume"} <= workflows


@pytest.mark.asyncio
async def test_job_discovery_workflow_handler_registers_tasks(monkeypatch):
    from careerpilot.acp.workflows import job_discovery as jd
    from careerpilot.mcp.base import McpToolResult

    async def fake_linkedin(db, *, tool_name, user_id, **kwargs):
        _ = db, user_id, kwargs
        if tool_name == "linkedin_connection_status":
            return McpToolResult(status="SUCCESS", result={"connected": False})
        return McpToolResult(status="ERROR", error={"code": "unexpected", "message": tool_name})

    async def fake_agent(db, *, user, filters):
        _ = db, user, filters
        return {
            "agent": "job_discovery",
            "agent_version": "v4",
            "discovered": 0,
            "created": 0,
            "updated": 0,
            "items": [],
            "tool_trace": [{"result": {"providers": ["demo"]}}],
            "warnings": [],
        }

    monkeypatch.setattr(jd, "call_linkedin_tool", fake_linkedin)
    monkeypatch.setattr(jd, "run_job_discovery_agent", fake_agent)

    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.get = AsyncMock(
        return_value=MagicMock(id=uuid.uuid4(), email="a@b.com", candidate_profile=None)
    )

    class _WF:
        id = uuid.uuid4()
        state: dict = {"steps": []}

    result = await jd.run_job_discovery_workflow(
        db,
        workflow=_WF(),  # type: ignore[arg-type]
        input_payload={"user_id": str(uuid.uuid4()), "include_demo": True, "limit": 5},
    )
    assert result.status == "completed"
    assert result.output.get("orchestration") == "acp+mcp"
    assert any(t["step"] == "search_providers" for t in result.tasks)
