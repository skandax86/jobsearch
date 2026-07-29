"""Deterministic resume section boundary detection (ATS-style pre-pass)."""

from __future__ import annotations

import re
from typing import Any

SECTION_KEYS = (
    "header",
    "summary",
    "experience",
    "projects",
    "education",
    "skills",
    "certifications",
    "awards",
    "languages",
    "publications",
)

_SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": (
        "summary",
        "professional summary",
        "professional overview",
        "overview",
        "profile",
        "about",
        "objective",
        "career objective",
        "about me",
    ),
    "skills": (
        "skills",
        "technical skills",
        "core skills",
        "key skills",
        "technologies",
        "tech stack",
        "competencies",
        "expertise",
    ),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "employment history",
        "work history",
        "career history",
    ),
    "projects": (
        "projects",
        "personal projects",
        "key projects",
        "selected projects",
        "academic projects",
    ),
    "education": (
        "education",
        "academic background",
        "academics",
        "qualifications",
    ),
    "certifications": (
        "certifications",
        "certificates",
        "licenses",
        "licenses & certifications",
        "licenses and certifications",
    ),
    "awards": (
        "awards",
        "honors",
        "honours",
        "achievements",
        "awards and honors",
    ),
    "languages": ("languages", "language skills"),
    "publications": ("publications", "papers", "research"),
}

# Longest aliases first so "professional overview" beats "overview".
_ALIAS_PATTERNS: list[tuple[str, re.Pattern[str]]] = []
for _key, _aliases in _SECTION_ALIASES.items():
    for _alias in sorted(_aliases, key=len, reverse=True):
        _ALIAS_PATTERNS.append(
            (
                _key,
                re.compile(
                    rf"^\s*{re.escape(_alias)}\s*(?:[:\-–—]\s*|$)",
                    re.I,
                ),
            )
        )


def number_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for idx, line in enumerate((text or "").splitlines(), start=1):
        lines.append((idx, line.rstrip()))
    return lines


def format_lined_text(text: str) -> str:
    return "\n".join(f"L{n:03d}|{line}" for n, line in number_lines(text))


def detect_section_name(line: str) -> str | None:
    """Return canonical section if the line is (or starts with) a known heading."""
    stripped = (line or "").strip()
    if not stripped or len(stripped) > 120:
        return None
    for key, pattern in _ALIAS_PATTERNS:
        if pattern.match(stripped):
            # Reject if this looks like a bullet/sentence using the word mid-line.
            if stripped.endswith(".") and len(stripped.split()) > 6:
                continue
            return key
    return None


def split_heading_remainder(line: str) -> tuple[str | None, str]:
    """
    If line is 'SKILLS Data Engineering: …' return ('skills', 'Data Engineering: …').
    If line is just 'SKILLS', return ('skills', '').
    """
    stripped = (line or "").strip()
    section = detect_section_name(stripped)
    if not section:
        return None, stripped
    for key, pattern in _ALIAS_PATTERNS:
        if key != section:
            continue
        match = pattern.match(stripped)
        if match:
            rest = stripped[match.end() :].strip(" :-–—")
            return section, rest
    return section, ""


def segment_resume_text(text: str) -> dict[str, Any]:
    """
    Split resume text into independent sections.

    A section ends when another known section heading begins.
    Content before the first heading is treated as header.
    Inline 'HEADING rest…' puts remainder into the new section.
    """
    lines = number_lines(text)
    sections: dict[str, list[tuple[int, str]]] = {key: [] for key in SECTION_KEYS}
    current = "header"
    seen_non_header = False

    for line_no, line in lines:
        stripped = line.strip()
        if not stripped:
            if sections[current] or current == "header":
                sections[current].append((line_no, line))
            continue

        section, remainder = split_heading_remainder(stripped)
        if section and section != current:
            current = section
            seen_non_header = True
            if remainder:
                sections[current].append((line_no, remainder))
            continue
        if section and section == current and remainder == "":
            # Pure heading line for the active section — skip.
            continue

        sections[current].append((line_no, line))

    out: dict[str, Any] = {
        "sections": {},
        "order": [],
        "line_count": len(lines),
    }
    for key in SECTION_KEYS:
        body_lines = sections[key]
        body = "\n".join(line for _, line in body_lines).strip()
        if not body and key != "header":
            continue
        if key == "header" and not body and seen_non_header:
            continue
        start = body_lines[0][0] if body_lines else None
        end = body_lines[-1][0] if body_lines else None
        out["sections"][key] = {
            "text": body,
            "start_line": start,
            "end_line": end,
            "line_ids": [f"L{n:03d}" for n, _ in body_lines if _.strip()],
        }
        out["order"].append(key)
    return out


def format_sections_for_prompt(segments: dict[str, Any]) -> str:
    blocks: list[str] = []
    for key in segments.get("order") or []:
        section = (segments.get("sections") or {}).get(key) or {}
        text = (section.get("text") or "").strip()
        if not text:
            continue
        start = section.get("start_line")
        end = section.get("end_line")
        span = f"L{start:03d}-L{end:03d}" if start and end else "unknown"
        blocks.append(f"### SECTION: {key.upper()} ({span})\n{text}")
    return "\n\n".join(blocks)


def section_lines(segments: dict[str, Any], key: str) -> list[str]:
    text = ((segments.get("sections") or {}).get(key) or {}).get("text") or ""
    return [ln.strip() for ln in text.splitlines() if ln.strip()]
