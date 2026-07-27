"""Job discovery API tests."""

from __future__ import annotations

import pytest


async def _auth_headers(client, unique_email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "securepass123", "display_name": "Seeker"},
    )
    assert response.status_code == 201, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_discover_demo_jobs_and_list(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    discover = await client.post(
        "/api/v1/jobs/discover",
        headers=headers,
        json={"query": "python", "include_demo": True, "include_remotive": False, "limit": 10},
    )
    assert discover.status_code == 200, discover.text
    data = discover.json()["data"]
    assert data["discovered"] >= 1
    assert data["created"] + data["updated"] >= 1
    assert data["items"]

    listed = await client.get("/api/v1/jobs", headers=headers, params={"q": "engineer"})
    assert listed.status_code == 200
    body = listed.json()["data"]
    assert body["total"] >= 1
    assert body["items"]

    job_id = body["items"][0]["id"]
    detail = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == job_id
    assert detail.json()["data"]["company"] is not None


@pytest.mark.asyncio
async def test_discover_is_idempotent_for_demo_source(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    payload = {"query": None, "include_demo": True, "include_remotive": False, "limit": 10}

    first = await client.post("/api/v1/jobs/discover", headers=headers, json=payload)
    assert first.status_code == 200
    created_first = first.json()["data"]["created"]

    second = await client.post("/api/v1/jobs/discover", headers=headers, json=payload)
    assert second.status_code == 200
    # Second run should mostly update existing demo sources.
    assert second.json()["data"]["updated"] >= 1
    assert second.json()["data"]["created"] <= created_first


@pytest.mark.asyncio
async def test_discover_with_experience_and_skills_filters(client, unique_email):
    headers = await _auth_headers(client, unique_email)

    discover = await client.post(
        "/api/v1/jobs/discover",
        headers=headers,
        json={
            "query": "engineer",
            "skills": ["Python"],
            "experience_level": "senior",
            "country": "us",
            "include_demo": True,
            "include_remotive": False,
            "limit": 10,
        },
    )
    assert discover.status_code == 200, discover.text
    items = discover.json()["data"]["items"]
    assert items
    assert all("senior" in (job["title"] or "").lower() for job in items)

    listed = await client.get(
        "/api/v1/jobs",
        headers=headers,
        params={"skills": "Python", "experience_level": "senior", "country": "us"},
    )
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_jobs_require_auth(client):
    response = await client.get("/api/v1/jobs")
    assert response.status_code == 401
