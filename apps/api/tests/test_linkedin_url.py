"""LinkedIn URL parsing / public fetch tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from careerpilot.domains.jobs.providers.linkedin_url import (
    LinkedInUrlError,
    canonicalize_linkedin_job_url,
    extract_linkedin_job_id,
    fetch_linkedin_job_from_url,
)


def test_extract_linkedin_job_id_from_view_url():
    assert (
        extract_linkedin_job_id("https://www.linkedin.com/jobs/view/4252026496/?trk=public")
        == "4252026496"
    )


def test_canonicalize_strips_tracking_query():
    long_url = (
        "https://www.linkedin.com/jobs/view/4442088705/"
        "?alternateChannel=search&eBP=" + ("x" * 800) + "&trackingId=abc"
    )
    assert canonicalize_linkedin_job_url(long_url) == (
        "https://www.linkedin.com/jobs/view/4442088705/"
    )


def test_extract_linkedin_job_id_from_current_job_param():
    assert (
        extract_linkedin_job_id(
            "https://www.linkedin.com/jobs/search/?currentJobId=3856789012&keywords=python"
        )
        == "3856789012"
    )


def test_extract_linkedin_job_id_rejects_bad_url():
    with pytest.raises(LinkedInUrlError) as exc:
        extract_linkedin_job_id("https://example.com/jobs/1")
    assert exc.value.code == "invalid_url"


@pytest.mark.asyncio
async def test_fetch_uses_description_override_when_guest_fails():
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.headers = {"content-type": "text/html"}
    mock_response.text = "forbidden"

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "careerpilot.domains.jobs.providers.linkedin_url.httpx.AsyncClient",
        return_value=mock_client,
    ):
        job = await fetch_linkedin_job_from_url(
            "https://www.linkedin.com/jobs/view/4252026496/",
            description_override=(
                "Senior Backend Engineer\nNeed Python, FastAPI, and Kubernetes."
            ),
        )

    assert job.external_id == "4252026496"
    assert job.provider == "linkedin"
    assert "Kubernetes" in (job.description or "") or "kubernetes" in str(
        (job.requirements or {}).get("skills", [])
    ).lower()


@pytest.mark.asyncio
async def test_fetch_real_google_job_from_linkedin():
    job = await fetch_linkedin_job_from_url(
        "https://www.linkedin.com/jobs/view/4442088705/"
        "?alternateChannel=search&eBP=" + ("x" * 200)
    )
    assert job.external_id == "4442088705"
    assert "Cloud Data Engineer" in job.title
    assert "Google" in job.company_name
    assert job.description and len(job.description) > 200
    skills = [s.lower() for s in (job.requirements or {}).get("skills", [])]
    assert any("python" in s for s in skills)
    assert any("spark" in s or "gcp" in s or "google cloud" in s for s in skills)
