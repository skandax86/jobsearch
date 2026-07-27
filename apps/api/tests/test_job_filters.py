"""Unit tests for job search filters."""

from __future__ import annotations

from careerpilot.domains.jobs.filters import (
    JobSearchFilters,
    filter_discovered_jobs,
    infer_experience_level,
    job_matches_filters,
)
from careerpilot.domains.jobs.providers.base import DiscoveredJob


def test_infer_senior_from_title():
    assert infer_experience_level("Senior Data Engineer", None) == "senior"
    assert infer_experience_level("Junior Backend Engineer", None) == "junior"


def test_skills_and_country_filters():
    filters = JobSearchFilters(skills=["Python", "Spark"], country="us")
    assert job_matches_filters(
        title="Senior Data Engineer",
        description="Build pipelines",
        location="Remote - US",
        remote_type="remote",
        requirements={"skills": ["Python", "SQL", "Spark"]},
        filters=filters,
    )
    assert not job_matches_filters(
        title="Backend Engineer",
        description="Java services",
        location="Bengaluru, India",
        remote_type="hybrid",
        requirements={"skills": ["Java"]},
        filters=filters,
    )


def test_filter_discovered_jobs_experience():
    jobs = [
        DiscoveredJob(
            provider="demo",
            external_id="1",
            title="Senior Data Engineer",
            company_name="A",
            description="5+ years",
            location="Remote - US",
            remote_type="remote",
            requirements={"skills": ["Python"]},
        ),
        DiscoveredJob(
            provider="demo",
            external_id="2",
            title="Junior Data Analyst",
            company_name="B",
            description="Entry level",
            location="Remote - US",
            remote_type="remote",
            requirements={"skills": ["SQL"]},
        ),
    ]
    out = filter_discovered_jobs(jobs, JobSearchFilters(experience_level="senior"))
    assert len(out) == 1
    assert out[0].external_id == "1"
