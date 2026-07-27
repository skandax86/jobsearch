"""Heuristic structuring of resume text into canonical Resume JSON."""

from __future__ import annotations

import re
from typing import Any

SCHEMA_VERSION = "1.0"

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s\-.]?)?(?:\(?\d{2,4}\)?[\s\-.]?)?\d{3,4}[\s\-.]?\d{3,4}")
URL_RE = re.compile(r"https?://[^\s)]+|www\.[^\s)]+|linkedin\.com/[^\s)]+", re.I)
DATE_RANGE_RE = re.compile(
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4})"
    r"\s*[-–—to]+\s*"
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4}|Present|Current|Now)",
    re.I,
)

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "profile", "professional summary", "about", "objective"),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "work history",
    ),
    "education": ("education", "academic", "academics"),
    "skills": ("skills", "technical skills", "core skills", "technologies", "tech stack"),
    "projects": ("projects", "personal projects", "selected projects"),
    "certifications": ("certifications", "certificates", "licenses"),
    "languages": ("languages", "language"),
}


def structure_resume_text(raw_text: str) -> dict[str, Any]:
    lines = _normalize_lines(raw_text)
    sections = _split_sections(lines)

    contact = _extract_contact(lines[:20], raw_text)
    headline = _guess_headline(lines, contact.get("name"))
    summary = _section_paragraph(sections.get("summary", []))
    experience = _parse_experience(sections.get("experience", []))
    education = _parse_education(sections.get("education", []))
    skills = _parse_skills(sections.get("skills", []))
    projects = _parse_simple_entries(sections.get("projects", []), prefix="project")
    certifications = _parse_simple_entries(
        sections.get("certifications", []), prefix="certification"
    )
    languages = _parse_skills(sections.get("languages", []))

    return {
        "schema_version": SCHEMA_VERSION,
        "contact": contact,
        "headline": headline,
        "summary": summary,
        "experience": experience,
        "education": education,
        "skills": skills,
        "projects": projects,
        "certifications": certifications,
        "languages": languages,
        "links": contact.get("links", []),
    }


def _normalize_lines(raw_text: str) -> list[str]:
    lines: list[str] = []
    for line in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        cleaned = re.sub(r"[ \t]+", " ", line).strip()
        if cleaned:
            lines.append(cleaned)
    return lines


def _canonical_section(line: str) -> str | None:
    key = re.sub(r"[^a-zA-Z ]+", "", line).strip().lower()
    if not key or len(key) > 40:
        return None
    for canonical, aliases in SECTION_ALIASES.items():
        if key in aliases:
            return canonical
    return None


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        section = _canonical_section(line)
        if section:
            current = section
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
    return sections


def _extract_contact(header_lines: list[str], raw_text: str) -> dict[str, Any]:
    email_match = EMAIL_RE.search(raw_text)
    phone_match = PHONE_RE.search(raw_text)
    links = list(dict.fromkeys(URL_RE.findall(raw_text)))[:10]

    name = None
    for line in header_lines[:5]:
        if EMAIL_RE.search(line) or PHONE_RE.search(line) or URL_RE.search(line):
            continue
        if _canonical_section(line):
            break
        if 2 <= len(line.split()) <= 5 and not line.endswith(":"):
            name = line
            break

    location = None
    for line in header_lines:
        if (
            any(token in line.lower() for token in (",", "remote"))
            and "@" not in line
            and not EMAIL_RE.search(line)
            and not PHONE_RE.search(line)
            and len(line) < 80
            and not _canonical_section(line)
        ):
            location = line
            break

    return {
        "name": name,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "location": location,
        "links": links,
    }


def _guess_headline(lines: list[str], name: str | None) -> str | None:
    for line in lines[:12]:
        if name and line == name:
            continue
        if EMAIL_RE.search(line) or PHONE_RE.search(line) or URL_RE.search(line):
            continue
        if _canonical_section(line):
            break
        if 1 <= len(line.split()) <= 8:
            return line
    return None


def _section_paragraph(lines: list[str]) -> str | None:
    if not lines:
        return None
    return " ".join(lines).strip() or None


def _parse_experience(lines: list[str]) -> list[dict[str, Any]]:
    blocks = _split_blocks(lines)
    experience: list[dict[str, Any]] = []
    for index, block in enumerate(blocks, start=1):
        if not block:
            continue
        header = block[0]
        dates = DATE_RANGE_RE.search(header) or DATE_RANGE_RE.search(" ".join(block[:3]))
        header_wo_dates = DATE_RANGE_RE.sub("", header).strip(" |·•-–—")
        title = None
        company = None
        if " at " in header_wo_dates.lower():
            left, right = re.split(r"\s+at\s+", header_wo_dates, maxsplit=1, flags=re.I)
            title, company = left.strip(" |-–—"), right.strip(" |-–—")
        elif " | " in header_wo_dates or " - " in header_wo_dates or " – " in header_wo_dates:
            parts = re.split(r"\s[\|\-–—]\s", header_wo_dates)
            if len(parts) >= 2:
                title, company = parts[0].strip(), parts[1].strip()
        else:
            title = header_wo_dates or header

        bullets = [ln.lstrip("•*-–— ").strip() for ln in block[1:] if ln.strip()]
        experience.append(
            {
                "id": f"experience_{index:02d}",
                "company": company,
                "title": title,
                "start_date": dates.group(1) if dates else None,
                "end_date": dates.group(2) if dates else None,
                "bullets": bullets,
                "source_fact_ids": [],
            }
        )
    return experience


def _parse_education(lines: list[str]) -> list[dict[str, Any]]:
    blocks = _split_blocks(lines)
    education: list[dict[str, Any]] = []
    for index, block in enumerate(blocks, start=1):
        if not block:
            continue
        education.append(
            {
                "id": f"education_{index:02d}",
                "institution": block[0],
                "degree": block[1] if len(block) > 1 else None,
                "details": block[2:],
                "source_fact_ids": [],
            }
        )
    return education


def _parse_skills(lines: list[str]) -> list[str]:
    skills: list[str] = []
    for line in lines:
        parts = re.split(r"[,|•;/]| and ", line)
        for part in parts:
            skill = part.strip(" -•*")
            if skill and len(skill) < 60:
                skills.append(skill)
    # Preserve order, drop duplicates
    return list(dict.fromkeys(skills))


def _parse_simple_entries(lines: list[str], *, prefix: str) -> list[dict[str, Any]]:
    blocks = _split_blocks(lines)
    entries: list[dict[str, Any]] = []
    for index, block in enumerate(blocks, start=1):
        if not block:
            continue
        entries.append(
            {
                "id": f"{prefix}_{index:02d}",
                "title": block[0],
                "details": block[1:],
                "source_fact_ids": [],
            }
        )
    return entries


def _split_blocks(lines: list[str]) -> list[list[str]]:
    """Split section lines into entry blocks using blank-like cues / date headers."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        starts_new = bool(DATE_RANGE_RE.search(line)) and current
        if starts_new:
            blocks.append(current)
            current = [line]
            continue
        # New block if previous ended and this looks like a header (short, no bullet)
        if (
            current
            and not line.startswith(("•", "-", "*", "–", "—"))
            and len(current) >= 2
            and len(line.split()) <= 10
            and DATE_RANGE_RE.search(line)
        ):
            blocks.append(current)
            current = [line]
            continue
        current.append(line)
    if current:
        blocks.append(current)
    return blocks
