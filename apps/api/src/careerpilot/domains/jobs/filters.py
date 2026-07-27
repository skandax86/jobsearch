"""Shared job discovery / catalog filters."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from careerpilot.domains.jobs.providers.base import DiscoveredJob

_SENIOR_RE = re.compile(r"\b(senior|sr\.?|staff|principal|lead|architect)\b", re.I)
_JUNIOR_RE = re.compile(r"\b(junior|jr\.?|entry[- ]?level|intern|graduate|associate)\b", re.I)
_MID_RE = re.compile(r"\b(mid[- ]?level|intermediate)\b", re.I)
_YEARS_RE = re.compile(r"(\d+)\+?\s*(?:\+|to|-)?\s*(?:\d+)?\s*years?", re.I)

_COUNTRY_ALIASES: dict[str, list[str]] = {
    "us": ["us", "usa", "united states", "america", "americas"],
    "usa": ["us", "usa", "united states", "america", "americas"],
    "uk": ["uk", "united kingdom", "britain", "england"],
    "india": ["india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "delhi"],
    "canada": ["canada"],
    "germany": ["germany", "deutschland"],
    "worldwide": ["worldwide", "anywhere", "global", "world", "oceania", "africa", "asia", "europe"],
}


@dataclass
class JobSearchFilters:
    query: str | None = None
    location: str | None = None
    country: str | None = None
    remote_type: str | None = None  # remote | hybrid | onsite | any
    skills: list[str] = field(default_factory=list)
    experience_level: str | None = None  # junior | mid | senior | any
    min_experience_years: int | None = None
    include_demo: bool = True
    include_remotive: bool = True
    include_naukri: bool = False
    limit: int = 20

    @classmethod
    def from_payload(cls, payload: Any) -> JobSearchFilters:
        skills_raw = getattr(payload, "skills", None) or []
        if isinstance(skills_raw, str):
            skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
        else:
            skills = [str(s).strip() for s in skills_raw if str(s).strip()]
        return cls(
            query=(getattr(payload, "query", None) or getattr(payload, "q", None) or None),
            location=(getattr(payload, "location", None) or None),
            country=(getattr(payload, "country", None) or None),
            remote_type=(getattr(payload, "remote_type", None) or None),
            skills=skills,
            experience_level=(getattr(payload, "experience_level", None) or None),
            min_experience_years=getattr(payload, "min_experience_years", None),
            include_demo=bool(getattr(payload, "include_demo", True)),
            include_remotive=bool(getattr(payload, "include_remotive", True)),
            include_naukri=bool(getattr(payload, "include_naukri", False)),
            limit=int(getattr(payload, "limit", 20) or 20),
        )

    @property
    def has_structured_filters(self) -> bool:
        return bool(
            self.location
            or self.country
            or (self.remote_type and self.remote_type.lower() not in {"", "any"})
            or self.skills
            or (self.experience_level and self.experience_level.lower() not in {"", "any"})
            or self.min_experience_years is not None
        )

    def provider_search_query(self) -> str | None:
        """Coarse text sent to Remotive/demo — keywords only (skills applied after)."""
        if self.query and self.query.strip():
            return self.query.strip()
        # Skills-only discovery: use first skill as a Remotive search hint
        if self.skills:
            return self.skills[0]
        return None


def _text_blob(*parts: str | None) -> str:
    return " ".join(p for p in parts if p).lower()


def infer_experience_level(title: str, description: str | None) -> str:
    blob = _text_blob(title, description)
    if _SENIOR_RE.search(blob):
        return "senior"
    if _JUNIOR_RE.search(blob):
        return "junior"
    if _MID_RE.search(blob):
        return "mid"
    years = _YEARS_RE.search(blob)
    if years:
        n = int(years.group(1))
        if n >= 5:
            return "senior"
        if n <= 2:
            return "junior"
        return "mid"
    return "mid"


def infer_min_years(title: str, description: str | None) -> int | None:
    blob = _text_blob(title, description)
    years = _YEARS_RE.search(blob)
    if years:
        return int(years.group(1))
    level = infer_experience_level(title, description)
    return {"junior": 0, "mid": 3, "senior": 5}.get(level)


def job_matches_filters(
    *,
    title: str,
    description: str | None,
    location: str | None,
    remote_type: str | None,
    requirements: dict[str, Any] | None,
    filters: JobSearchFilters,
    apply_query: bool = True,
) -> bool:
    if apply_query and filters.query:
        q = filters.query.strip().lower()
        blob = _text_blob(title, description, location)
        if q not in blob:
            return False

    if filters.location:
        loc = (location or "").lower()
        if filters.location.strip().lower() not in loc:
            return False

    if filters.country:
        blob = _text_blob(location, description)
        country = filters.country.strip().lower()
        needles = _COUNTRY_ALIASES.get(country, [country])
        if not any(n in blob for n in needles):
            return False

    if filters.remote_type and filters.remote_type.lower() not in {"any", ""}:
        rt = (remote_type or "").lower()
        want = filters.remote_type.lower()
        if want == "remote":
            if rt and rt not in {"remote", "worldwide"}:
                return False
        elif rt != want:
            return False

    if filters.skills:
        req_skills: list[str] = []
        if isinstance(requirements, dict):
            raw = requirements.get("skills") or []
            if isinstance(raw, list):
                req_skills = [str(s) for s in raw]
        blob = _text_blob(title, description, " ".join(req_skills))
        # At least one requested skill must appear
        if not any(s.lower() in blob for s in filters.skills):
            return False

    if filters.experience_level and filters.experience_level.lower() not in {"any", ""}:
        # Skip title heuristics for Naukri-sourced postings (years applied at search time).
        is_naukri = isinstance(requirements, dict) and requirements.get("source") == "naukri"
        if not is_naukri:
            level = infer_experience_level(title, description)
            if level != filters.experience_level.lower():
                return False

    if filters.min_experience_years is not None:
        is_naukri = isinstance(requirements, dict) and requirements.get("source") == "naukri"
        if not is_naukri:
            years = infer_min_years(title, description)
            if years is not None and years < filters.min_experience_years:
                if infer_experience_level(title, description) == "junior":
                    return False

    return True


def filter_discovered_jobs(
    jobs: list[DiscoveredJob],
    filters: JobSearchFilters,
    *,
    apply_query: bool = False,
) -> list[DiscoveredJob]:
    """Filter provider results. Query often already applied by Remotive/demo."""
    out: list[DiscoveredJob] = []
    for job in jobs:
        # Naukri already filtered by experience years at the source; title
        # heuristics ("junior"/"senior") incorrectly drop plain "Data Engineer".
        effective = filters
        if job.provider == "naukri" and filters.experience_level:
            effective = JobSearchFilters(
                query=filters.query,
                location=filters.location,
                country=filters.country,
                remote_type=filters.remote_type,
                skills=filters.skills,
                experience_level=None,
                min_experience_years=None,
                include_demo=filters.include_demo,
                include_remotive=filters.include_remotive,
                include_naukri=filters.include_naukri,
                limit=filters.limit,
            )
        if job_matches_filters(
            title=job.title,
            description=job.description,
            location=job.location,
            remote_type=job.remote_type,
            requirements=job.requirements,
            filters=effective,
            apply_query=apply_query,
        ):
            out.append(job)
    return out
