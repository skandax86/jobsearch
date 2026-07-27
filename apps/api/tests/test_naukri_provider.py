"""Naukri provider unit tests (mocked — no live login)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from careerpilot.domains.jobs.providers import naukri as naukri_provider


def test_naukri_root_points_at_tools():
    assert naukri_provider._NAUKRI_ROOT.name == "naukri-mcp"
    assert (naukri_provider._NAUKRI_ROOT.parent.name) == "tools"


@pytest.mark.asyncio
async def test_fetch_naukri_jobs_maps_results():
    fake_job = SimpleNamespace(
        id="123",
        title="Data Engineer",
        company="IBM",
        location="Bengaluru",
        url="https://www.naukri.com/job/123",
        skills_required=["Python", "SQL"],
        salary="Not disclosed",
        found_at=None,
        match_score=12,
        model_dump=lambda mode="json": {"id": "123", "title": "Data Engineer"},
    )

    client = MagicMock()
    client.start = AsyncMock()
    client.stop = AsyncMock()
    client.search_jobs = AsyncMock(return_value=[fake_job])

    with (
        patch.object(naukri_provider, "naukri_available", return_value={"ready": True}),
        patch.object(naukri_provider, "_ensure_naukri_import", return_value=lambda **_: client),
    ):
        jobs, err = await naukri_provider.fetch_naukri_jobs(
            query="data engineer",
            location="Bengaluru",
            skills=["Python"],
            limit=5,
        )

    assert err is None
    assert len(jobs) == 1
    assert jobs[0].provider == "naukri"
    assert jobs[0].external_id == "123"
    assert jobs[0].title == "Data Engineer"
    assert jobs[0].company_name == "IBM"
    assert "Python" in (jobs[0].requirements or {}).get("skills", [])
    client.search_jobs.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_naukri_skips_when_not_ready():
    with patch.object(
        naukri_provider,
        "naukri_available",
        return_value={"ready": False, "hint": "missing"},
    ):
        jobs, err = await naukri_provider.fetch_naukri_jobs(query="x")
    assert jobs == []
    assert err == "missing"
