"""Naukri.com job provider — wraps tools/naukri-mcp client for discovery."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from careerpilot.config import settings
from careerpilot.domains.jobs.providers.base import DiscoveredJob

logger = logging.getLogger(__name__)

# .../apps/api/src/careerpilot/domains/jobs/providers/naukri.py → repo root is parents[7]
_NAUKRI_ROOT = Path(__file__).resolve().parents[7] / "tools" / "naukri-mcp"


def naukri_configured() -> bool:
    return bool(settings.naukri_email.strip() and settings.naukri_password.strip())


def naukri_available() -> dict[str, Any]:
    """Status for dashboard / health."""
    configured = naukri_configured()
    client_ok = False
    playwright_ok = False
    root_ok = _NAUKRI_ROOT.is_dir() and (_NAUKRI_ROOT / "naukri.py").is_file()
    if root_ok:
        try:
            _ensure_naukri_import()
            client_ok = True
        except Exception as exc:
            logger.debug("Naukri import failed: %s", exc)
        try:
            import playwright  # noqa: F401

            playwright_ok = True
        except ImportError:
            playwright_ok = False
    return {
        "provider": "naukri",
        "configured": configured,
        "package_present": root_ok,
        "import_ok": client_ok,
        "playwright_ok": playwright_ok,
        "ready": configured and root_ok and client_ok and playwright_ok,
        "default_location": settings.naukri_default_location,
        "hint": None
        if configured and root_ok and client_ok and playwright_ok
        else _hint(configured, root_ok, client_ok, playwright_ok),
    }


def _hint(configured: bool, root_ok: bool, client_ok: bool, playwright_ok: bool) -> str:
    if not root_ok:
        return "Run: make naukri-mcp-setup"
    if not configured:
        return "Set NAUKRI_EMAIL and NAUKRI_PASSWORD in .env.naukri (or .env)"
    if not client_ok or not playwright_ok:
        return "Install API naukri extras: cd apps/api && pip install -e '.[naukri]' && playwright install chromium"
    return "Naukri not ready"


def _ensure_naukri_import():
    root = str(_NAUKRI_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from naukri import NaukriClient  # type: ignore  # noqa: F401

    return NaukriClient


def _experience_years(
    *,
    experience_level: str | None,
    min_experience_years: int | None,
) -> str:
    if min_experience_years is not None:
        return str(max(0, min_experience_years))
    level = (experience_level or "").lower()
    mapping = {"junior": "1", "mid": "3", "senior": "5", "any": None, "": None}
    if level in mapping and mapping[level] is not None:
        return mapping[level]  # type: ignore[return-value]
    return str(settings.naukri_default_experience_years)


def _resolve_location(*, location: str | None, country: str | None) -> str:
    if location and location.strip():
        return location.strip()
    country_l = (country or "").strip().lower()
    if country_l in {"india", "in"}:
        return settings.naukri_default_location or "Bengaluru"
    return settings.naukri_default_location or "Bengaluru"


def _infer_remote_type(location: str) -> str | None:
    loc = location.lower()
    if "hybrid" in loc:
        return "hybrid"
    if "remote" in loc or "work from home" in loc or "wfh" in loc:
        return "remote"
    return "onsite"


def _map_job(job: Any) -> DiscoveredJob:
    job_id = str(getattr(job, "id", None) or getattr(job, "job_id", "") or "")
    title = str(getattr(job, "title", None) or "Untitled role")
    company = str(getattr(job, "company", None) or "Unknown company")
    location = str(getattr(job, "location", None) or "")
    url = getattr(job, "url", None)
    skills = list(getattr(job, "skills_required", None) or [])
    salary = getattr(job, "salary", None)
    match_score = getattr(job, "match_score", None)
    return DiscoveredJob(
        provider="naukri",
        external_id=job_id or f"{company}:{title}",
        title=title,
        company_name=company,
        description=None,
        location=location or None,
        remote_type=_infer_remote_type(location) if location else None,
        canonical_url=url,
        source_url=url,
        posted_at=getattr(job, "found_at", None),
        compensation={"salary": salary} if salary else None,
        requirements={
            "skills": skills,
            "match_score": match_score,
            "source": "naukri",
        },
        company_industry=None,
        raw_payload=job.model_dump(mode="json") if hasattr(job, "model_dump") else {},
    )


async def fetch_naukri_jobs(
    *,
    query: str | None = None,
    location: str | None = None,
    country: str | None = None,
    skills: list[str] | None = None,
    experience_level: str | None = None,
    min_experience_years: int | None = None,
    limit: int = 20,
) -> tuple[list[DiscoveredJob], str | None]:
    """Search Naukri and map to DiscoveredJob. Returns (jobs, error_message)."""
    status = naukri_available()
    if not status["ready"]:
        hint = status.get("hint") or "Naukri not ready"
        logger.warning("Naukri skip: %s", hint)
        return [], hint

    title = (query or "").strip() or "software engineer"
    loc = _resolve_location(location=location, country=country)
    experience = _experience_years(
        experience_level=experience_level,
        min_experience_years=min_experience_years,
    )
    skill_list = [s for s in (skills or []) if s] or [
        s.strip() for s in settings.naukri_default_skills.split(",") if s.strip()
    ]

    NaukriClient = _ensure_naukri_import()
    client = NaukriClient(
        email=settings.naukri_email,
        password=settings.naukri_password,
    )
    try:
        await client.start()
        logger.info(
            "Naukri search title=%r location=%r experience=%r skills=%s limit=%s",
            title,
            loc,
            experience,
            skill_list,
            limit,
        )
        jobs = await client.search_jobs(
            title=title,
            location=loc,
            experience=experience,
            skills=skill_list,
            max_results=limit,
        )
    except Exception as exc:
        logger.warning("Naukri search failed: %s", exc, exc_info=True)
        return [], f"Naukri search failed: {exc}"
    finally:
        try:
            await client.stop()
        except Exception:
            pass

    mapped = [_map_job(job) for job in jobs[:limit]]
    logger.info("Naukri search returned %s jobs", len(mapped))
    return mapped, None
