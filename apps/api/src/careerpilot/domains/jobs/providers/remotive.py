"""Remotive public job API provider (no API key required)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from careerpilot.domains.jobs.providers.base import DiscoveredJob

logger = logging.getLogger(__name__)

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"


def _parse_posted_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Remotive uses e.g. 2024-01-15T12:00:00
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        return None


def _map_job(item: dict[str, Any]) -> DiscoveredJob:
    external_id = str(item.get("id") or item.get("url") or item.get("title"))
    tags = item.get("tags") or []
    return DiscoveredJob(
        provider="remotive",
        external_id=external_id,
        title=str(item.get("title") or "Untitled role"),
        company_name=str(item.get("company_name") or "Unknown company"),
        description=item.get("description"),
        location=item.get("candidate_required_location") or "Remote",
        remote_type="remote",
        canonical_url=item.get("url"),
        source_url=item.get("url"),
        posted_at=_parse_posted_at(item.get("publication_date")),
        compensation={"salary": item.get("salary")} if item.get("salary") else None,
        requirements={
            "skills": tags,
            "job_type": item.get("job_type"),
            "category": item.get("category"),
        },
        company_website=None,
        company_industry=item.get("category"),
        raw_payload=item,
    )


async def fetch_remotive_jobs(query: str | None = None, *, limit: int = 20) -> list[DiscoveredJob]:
    params: dict[str, str] = {}
    if query:
        params["search"] = query
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(REMOTIVE_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except Exception:
        logger.warning("Remotive fetch failed", exc_info=True)
        return []

    jobs_raw = payload.get("jobs") or []
    jobs = [_map_job(item) for item in jobs_raw[:limit]]
    return jobs
