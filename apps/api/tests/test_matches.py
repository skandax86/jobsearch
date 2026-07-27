"""Job matching API tests."""

from __future__ import annotations

import hashlib
import json
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from careerpilot.db.session import AsyncSessionLocal
from careerpilot.domains.candidate.models import CandidateProfile
from careerpilot.domains.identity.models import User
from careerpilot.domains.resume.models import Resume, ResumeContent, ResumeVersion


async def _auth_headers(client, unique_email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "securepass123", "display_name": "Matcher"},
    )
    assert response.status_code == 201, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _seed_parsed_resume(email: str) -> uuid.UUID:
    content = {
        "schema_version": "1.0",
        "headline": "Senior Data Engineer",
        "summary": "Pipelines and analytics infrastructure",
        "skills": ["Python", "SQL", "Spark", "Airflow", "BigQuery", "FastAPI"],
        "experience": [
            {
                "title": "Data Engineer",
                "company": "Example Co",
                "bullets": ["Built Spark jobs and Airflow DAGs on BigQuery"],
            }
        ],
    }
    checksum = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()

    async with AsyncSessionLocal() as db:
        user = await db.scalar(
            select(User).where(User.email == email).options(selectinload(User.candidate_profile))
        )
        assert user is not None
        profile = user.candidate_profile
        if profile is None:
            profile = await db.scalar(
                select(CandidateProfile).where(CandidateProfile.user_id == user.id)
            )
        assert profile is not None

        resume = Resume(
            candidate_profile_id=profile.id,
            title="Seeded resume",
            status="extracted",
        )
        version = ResumeVersion(
            resume=resume,
            version_number=1,
            kind="source",
            status="extracted",
        )
        db.add(resume)
        await db.flush()

        resume_content = ResumeContent(
            schema_version="1.0",
            content=content,
            content_checksum=checksum,
        )
        db.add(resume_content)
        await db.flush()
        version.content_id = resume_content.id
        resume.active_version_id = version.id
        await db.commit()
        return resume.id


@pytest.mark.asyncio
async def test_run_matching_and_list(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    resume_id = await _seed_parsed_resume(unique_email)

    discover = await client.post(
        "/api/v1/jobs/discover",
        headers=headers,
        json={"include_demo": True, "include_remotive": False, "limit": 10},
    )
    assert discover.status_code == 200, discover.text

    run = await client.post(
        "/api/v1/matches/run",
        headers=headers,
        json={"resume_id": str(resume_id), "limit": 20, "min_score": 0.0},
    )
    assert run.status_code == 200, run.text
    data = run.json()["data"]
    assert data["scored"] >= 1
    assert data["matched"] >= 1
    assert data["items"]
    assert data["items"][0]["score"] >= data["items"][-1]["score"]
    assert data["items"][0]["explanation"] is not None
    assert data["items"][0]["job"] is not None

    listed = await client.get("/api/v1/matches", headers=headers)
    assert listed.status_code == 200
    body = listed.json()["data"]
    assert body["total"] >= 1

    match_id = body["items"][0]["id"]
    detail = await client.get(f"/api/v1/matches/{match_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == match_id


@pytest.mark.asyncio
async def test_matching_requires_parsed_resume(client, unique_email):
    headers = await _auth_headers(client, unique_email)
    await client.post(
        "/api/v1/jobs/discover",
        headers=headers,
        json={"include_demo": True, "include_remotive": False, "limit": 5},
    )
    response = await client.post("/api/v1/matches/run", headers=headers, json={})
    assert response.status_code == 400
    assert response.json()["errors"][0]["code"] in {"resume_missing", "resume_not_parsed"}


@pytest.mark.asyncio
async def test_matches_require_auth(client):
    response = await client.get("/api/v1/matches")
    assert response.status_code == 401
