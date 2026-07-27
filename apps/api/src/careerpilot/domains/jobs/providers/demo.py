"""Demo job provider for offline/local development."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from careerpilot.domains.jobs.providers.base import DiscoveredJob

DEMO_JOBS: list[DiscoveredJob] = [
    DiscoveredJob(
        provider="demo",
        external_id="demo-data-engineer-1",
        title="Senior Data Engineer",
        company_name="Northwind Analytics",
        description=(
            "Build reliable batch and streaming pipelines on BigQuery and Spark. "
            "Own data quality, observability, and partner with analytics teams."
        ),
        location="Remote - US",
        remote_type="remote",
        canonical_url="https://example.com/jobs/senior-data-engineer",
        source_url="https://example.com/jobs/senior-data-engineer",
        posted_at=datetime.now(UTC) - timedelta(days=2),
        compensation={"currency": "USD", "min": 160000, "max": 200000},
        requirements={"skills": ["Python", "SQL", "Spark", "BigQuery", "Airflow"]},
        company_website="https://example.com",
        company_industry="Software",
        raw_payload={"source": "demo"},
    ),
    DiscoveredJob(
        provider="demo",
        external_id="demo-backend-1",
        title="Backend Engineer (Python/FastAPI)",
        company_name="Harbor Systems",
        description=(
            "Design and ship APIs for a multi-tenant SaaS platform. "
            "Experience with Postgres, Redis, and cloud deployments preferred."
        ),
        location="Bengaluru, India",
        remote_type="hybrid",
        canonical_url="https://example.com/jobs/backend-engineer",
        source_url="https://example.com/jobs/backend-engineer",
        posted_at=datetime.now(UTC) - timedelta(days=5),
        compensation={"currency": "INR", "min": 2500000, "max": 4000000},
        requirements={"skills": ["Python", "FastAPI", "PostgreSQL", "Redis"]},
        company_website="https://harbor.example.com",
        company_industry="SaaS",
        raw_payload={"source": "demo"},
    ),
    DiscoveredJob(
        provider="demo",
        external_id="demo-platform-1",
        title="Software Engineer - Data Platform",
        company_name="Lattice Labs",
        description=(
            "Work on ingestion, transformation, and serving layers for internal data products. "
            "Strong ownership mindset and production debugging skills required."
        ),
        location="Remote - Worldwide",
        remote_type="remote",
        canonical_url="https://example.com/jobs/data-platform",
        source_url="https://example.com/jobs/data-platform",
        posted_at=datetime.now(UTC) - timedelta(days=1),
        requirements={"skills": ["Python", "Kafka", "dbt", "Kubernetes"]},
        company_industry="AI",
        raw_payload={"source": "demo"},
    ),
]


def fetch_demo_jobs(query: str | None = None) -> list[DiscoveredJob]:
    q = (query or "").strip().lower()
    if not q:
        return list(DEMO_JOBS)
    return [
        job
        for job in DEMO_JOBS
        if q in job.title.lower()
        or q in job.company_name.lower()
        or q in (job.description or "").lower()
        or any(q in skill.lower() for skill in (job.requirements or {}).get("skills", []))
    ]
