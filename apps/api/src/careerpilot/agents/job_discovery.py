"""Job Discovery agent — Remotive / demo / Naukri (LinkedIn via Cursor MCP)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.domains.identity.models import User
from careerpilot.domains.jobs.filters import JobSearchFilters
from careerpilot.domains.jobs.service import discover_jobs

AGENT_NAME = "job_discovery"
AGENT_VERSION = "v4"


async def run_job_discovery_agent(
    db: AsyncSession,
    *,
    user: User,
    filters: JobSearchFilters | None = None,
    query: str | None = None,
    include_demo: bool = True,
    include_remotive: bool = True,
    include_naukri: bool = False,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Discover jobs via Remotive, demo, and optional Naukri.

    Personal LinkedIn tools live in Cursor MCP (`mcp-server-linkedin`).
    """
    _ = user
    search = filters or JobSearchFilters(
        query=query,
        include_demo=include_demo,
        include_remotive=include_remotive,
        include_naukri=include_naukri,
        limit=limit,
    )
    effective_query = (search.query or "").strip() or None
    warnings: list[str] = [
        "LinkedIn scraping/search runs in Cursor MCP (mcp-server-linkedin), "
        "not the dashboard.",
    ]
    providers = []
    if search.include_remotive:
        providers.append("remotive")
    if search.include_naukri:
        providers.append("naukri")
    if search.include_demo:
        providers.append("demo")

    tool_trace: list[dict[str, Any]] = [
        {
            "tool": "job_providers_discover",
            "status": "SUCCESS",
            "result": {
                "providers": providers,
                "include_demo": search.include_demo,
                "include_remotive": search.include_remotive,
                "include_naukri": search.include_naukri,
                "query": effective_query,
                "location": search.location,
                "country": search.country,
                "remote_type": search.remote_type,
                "skills": search.skills,
                "experience_level": search.experience_level,
                "min_experience_years": search.min_experience_years,
            },
        }
    ]

    discovery = await discover_jobs(db, filters=search)
    warnings.extend(discovery.get("warnings") or [])

    return {
        "agent": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "query_used": effective_query,
        "filters_used": {
            "location": search.location,
            "country": search.country,
            "remote_type": search.remote_type,
            "skills": search.skills,
            "experience_level": search.experience_level,
            "min_experience_years": search.min_experience_years,
            "include_naukri": search.include_naukri,
        },
        "linkedin_connected": False,
        "linkedin_profile": None,
        "warnings": warnings,
        "tool_trace": tool_trace,
        "discovered": discovery["discovered"],
        "created": discovery["created"],
        "updated": discovery["updated"],
        "items": discovery["items"],
        "confidence": 0.65 if search.include_naukri else 0.6,
        "outcome": "completed",
    }
