"""Canonical CareerPilot resume / profile JSON schema (shared backbone)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = "1.1"

EMPTY_CONTACT: dict[str, Any] = {
    "name": None,
    "email": None,
    "phone": None,
    "location": None,
    "links": [],
}


def empty_resume_content() -> dict[str, Any]:
    """Standard backbone used by uploads, tailored saves, and profile."""
    return {
        "schema_version": SCHEMA_VERSION,
        "contact": deepcopy(EMPTY_CONTACT),
        "headline": None,
        "summary": None,
        "experience": [],
        "education": [],
        "skills": [],
        "projects": [],
        "certifications": [],
        "awards": [],
        "languages": [],
        "hobbies": [],
        "personal": {
            "job_title": None,
            "work_authorization": None,
            "notes": None,
        },
        "links": [],
    }


def empty_experience_entry() -> dict[str, Any]:
    return {
        "id": f"experience_{uuid4().hex[:8]}",
        "company": None,
        "title": None,
        "location": None,
        "start_date": None,
        "end_date": None,
        "is_current": False,
        "summary": None,
        "bullets": [],
        "source_fact_ids": [],
    }


def empty_education_entry() -> dict[str, Any]:
    return {
        "id": f"education_{uuid4().hex[:8]}",
        "institution": None,
        "degree": None,
        "specialization": None,
        "location": None,
        "start_date": None,
        "end_date": None,
        "is_current": False,
        "score": None,
        "score_type": None,
        "summary": None,
        "details": [],
        "source_fact_ids": [],
    }


def empty_project_entry() -> dict[str, Any]:
    return {
        "id": f"project_{uuid4().hex[:8]}",
        "title": None,
        "organization": None,
        "url": None,
        "location": None,
        "start_date": None,
        "end_date": None,
        "is_current": False,
        "summary": None,
        "bullets": [],
        "technologies": [],
        "source_fact_ids": [],
    }


def empty_certification_entry() -> dict[str, Any]:
    return {
        "id": f"certification_{uuid4().hex[:8]}",
        "title": None,
        "issuer": None,
        "date": None,
        "expiry_date": None,
        "credential_id": None,
        "url": None,
        "summary": None,
        "source_fact_ids": [],
    }


def empty_award_entry() -> dict[str, Any]:
    return {
        "id": f"award_{uuid4().hex[:8]}",
        "title": None,
        "issuer": None,
        "date": None,
        "summary": None,
        "source_fact_ids": [],
    }


def normalize_resume_content(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Coerce arbitrary content into the shared schema without dropping known fields."""
    base = empty_resume_content()
    if not isinstance(raw, dict):
        return base

    contact_in = raw.get("contact") if isinstance(raw.get("contact"), dict) else {}
    personal_in = raw.get("personal") if isinstance(raw.get("personal"), dict) else {}

    base["schema_version"] = str(raw.get("schema_version") or SCHEMA_VERSION)
    base["contact"] = {
        "name": _str_or_none(contact_in.get("name")),
        "email": _str_or_none(contact_in.get("email")),
        "phone": _str_or_none(contact_in.get("phone")),
        "location": _str_or_none(contact_in.get("location")),
        "links": _str_list(contact_in.get("links") or raw.get("links")),
    }
    base["headline"] = _str_or_none(raw.get("headline") or personal_in.get("job_title"))
    base["summary"] = _str_or_none(raw.get("summary"))
    base["experience"] = [_normalize_experience(item) for item in _list_of_dicts(raw.get("experience"))]
    base["education"] = [_normalize_education(item) for item in _list_of_dicts(raw.get("education"))]
    base["skills"] = _skills(raw.get("skills"))
    base["projects"] = [_normalize_project(item) for item in _list_of_dicts(raw.get("projects"))]
    base["certifications"] = [
        _normalize_certification(item) for item in _list_of_dicts(raw.get("certifications"))
    ]
    base["awards"] = [_normalize_award(item) for item in _list_of_dicts(raw.get("awards"))]
    base["languages"] = _skills(raw.get("languages"))
    base["hobbies"] = _skills(raw.get("hobbies"))
    base["personal"] = {
        "job_title": _str_or_none(personal_in.get("job_title") or raw.get("headline")),
        "work_authorization": _str_or_none(personal_in.get("work_authorization")),
        "notes": _str_or_none(personal_in.get("notes")),
    }
    base["links"] = _str_list(raw.get("links") or base["contact"]["links"])
    return base


def resume_origin(resume: Any) -> str:
    """uploaded = has source file; generated = saved from tailor/profile without upload."""
    if getattr(resume, "source_object_key", None):
        return "uploaded"
    return "generated"


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "present", "current"}
    return default


def _str_list(value: Any) -> list[str]:
    if isinstance(value, str):
        parts = [p.strip() for p in value.replace("\n", ",").split(",")]
        return [p for p in parts if p]
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def _skills(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        elif isinstance(item, dict):
            name = item.get("name") or item.get("skill")
            if isinstance(name, str) and name.strip():
                out.append(name.strip())
    return out


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _entry_id(raw: dict[str, Any], prefix: str) -> str:
    existing = _str_or_none(raw.get("id"))
    return existing or f"{prefix}_{uuid4().hex[:8]}"


def _normalize_experience(raw: dict[str, Any]) -> dict[str, Any]:
    end_date = _str_or_none(raw.get("end_date"))
    is_current = _bool(raw.get("is_current"))
    if end_date and end_date.lower() in {"present", "current", "now"}:
        is_current = True
        end_date = None
    return {
        "id": _entry_id(raw, "experience"),
        "company": _str_or_none(raw.get("company") or raw.get("organization")),
        "title": _str_or_none(raw.get("title") or raw.get("role") or raw.get("job_title")),
        "location": _str_or_none(raw.get("location")),
        "start_date": _str_or_none(raw.get("start_date") or raw.get("start")),
        "end_date": None if is_current else end_date,
        "is_current": is_current,
        "summary": _str_or_none(raw.get("summary") or raw.get("description")),
        "bullets": _str_list(raw.get("bullets") or raw.get("achievements") or raw.get("details")),
        "source_fact_ids": list(raw.get("source_fact_ids") or [])
        if isinstance(raw.get("source_fact_ids"), list)
        else [],
    }


def _normalize_education(raw: dict[str, Any]) -> dict[str, Any]:
    end_date = _str_or_none(raw.get("end_date") or raw.get("graduation_date") or raw.get("year"))
    is_current = _bool(raw.get("is_current"))
    if end_date and end_date.lower() in {"present", "current", "now"}:
        is_current = True
        end_date = None
    details = raw.get("details")
    detail_list = _str_list(details) if not isinstance(details, list) or (
        details and isinstance(details[0], str)
    ) else _str_list([str(d) for d in details if d is not None])
    return {
        "id": _entry_id(raw, "education"),
        "institution": _str_or_none(
            raw.get("institution") or raw.get("school") or raw.get("college") or raw.get("university")
        ),
        "degree": _str_or_none(raw.get("degree") or raw.get("title")),
        "specialization": _str_or_none(
            raw.get("specialization") or raw.get("field") or raw.get("major")
        ),
        "location": _str_or_none(raw.get("location")),
        "start_date": _str_or_none(raw.get("start_date") or raw.get("start")),
        "end_date": None if is_current else end_date,
        "is_current": is_current,
        "score": _str_or_none(raw.get("score") or raw.get("gpa") or raw.get("cgpa")),
        "score_type": _str_or_none(raw.get("score_type") or raw.get("grade_scale")),
        "summary": _str_or_none(raw.get("summary") or raw.get("description")),
        "details": detail_list,
        "source_fact_ids": list(raw.get("source_fact_ids") or [])
        if isinstance(raw.get("source_fact_ids"), list)
        else [],
    }


def _normalize_project(raw: dict[str, Any]) -> dict[str, Any]:
    end_date = _str_or_none(raw.get("end_date"))
    is_current = _bool(raw.get("is_current"))
    if end_date and end_date.lower() in {"present", "current", "now"}:
        is_current = True
        end_date = None
    details = raw.get("details")
    bullets = raw.get("bullets")
    if not bullets and isinstance(details, list):
        bullets = details
    return {
        "id": _entry_id(raw, "project"),
        "title": _str_or_none(raw.get("title") or raw.get("name")),
        "organization": _str_or_none(raw.get("organization") or raw.get("company")),
        "url": _str_or_none(raw.get("url") or raw.get("link")),
        "location": _str_or_none(raw.get("location")),
        "start_date": _str_or_none(raw.get("start_date") or raw.get("start")),
        "end_date": None if is_current else end_date,
        "is_current": is_current,
        "summary": _str_or_none(raw.get("summary") or raw.get("description")),
        "bullets": _str_list(bullets),
        "technologies": _skills(raw.get("technologies") or raw.get("tech") or raw.get("skills")),
        "source_fact_ids": list(raw.get("source_fact_ids") or [])
        if isinstance(raw.get("source_fact_ids"), list)
        else [],
    }


def _normalize_certification(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _entry_id(raw, "certification"),
        "title": _str_or_none(raw.get("title") or raw.get("name")),
        "issuer": _str_or_none(raw.get("issuer") or raw.get("organization") or raw.get("authority")),
        "date": _str_or_none(raw.get("date") or raw.get("issued_date") or raw.get("start_date")),
        "expiry_date": _str_or_none(raw.get("expiry_date") or raw.get("end_date")),
        "credential_id": _str_or_none(raw.get("credential_id") or raw.get("credentialId")),
        "url": _str_or_none(raw.get("url") or raw.get("link")),
        "summary": _str_or_none(raw.get("summary") or raw.get("description")),
        "source_fact_ids": list(raw.get("source_fact_ids") or [])
        if isinstance(raw.get("source_fact_ids"), list)
        else [],
    }


def _normalize_award(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _entry_id(raw, "award"),
        "title": _str_or_none(raw.get("title") or raw.get("name")),
        "issuer": _str_or_none(raw.get("issuer") or raw.get("organization")),
        "date": _str_or_none(raw.get("date") or raw.get("year")),
        "summary": _str_or_none(raw.get("summary") or raw.get("description")),
        "source_fact_ids": list(raw.get("source_fact_ids") or [])
        if isinstance(raw.get("source_fact_ids"), list)
        else [],
    }
