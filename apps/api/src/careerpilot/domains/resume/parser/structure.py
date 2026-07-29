"""Rule-based resume structuring (ATS hybrid): section split → per-section extractors."""

from __future__ import annotations

import re
from typing import Any

from careerpilot.domains.resume.parser.sections import (
    detect_section_name,
    section_lines,
    segment_resume_text,
)
from careerpilot.domains.resume.schema import SCHEMA_VERSION, normalize_resume_content

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s\-.]*)?(?:\(?\d{2,5}\)?[\s\-.]*)?\d{3,5}[\s\-.]?\d{3,5}"
)
URL_RE = re.compile(
    r"(?:https?://[^\s)|]+|www\.[^\s)|]+|linkedin\.com/[^\s)|]+|github\.com/[^\s)|]+)",
    re.I,
)

MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
DATE_TOKEN = rf"(?:{MONTH}\.?\s+\d{{4}}|\d{{4}})"
PRESENT = r"(?:Present|Current|Now)"
DATE_RANGE_RE = re.compile(
    rf"({DATE_TOKEN})\s*[-–—to]+\s*({DATE_TOKEN}|{PRESENT})",
    re.I,
)
# Trailing date range at end of a header line
TRAILING_DATE_RE = re.compile(
    rf"\s+({DATE_TOKEN})\s*[-–—to]+\s*({DATE_TOKEN}|{PRESENT})\s*$",
    re.I,
)
# Single end/graduation date like "Sep 2024" or "Oct 2022"
SINGLE_DATE_RE = re.compile(rf"\b({DATE_TOKEN}|{PRESENT})\b", re.I)
CGPA_RE = re.compile(
    r"(?:(?:CGPA|GPA)\s*[:|]?\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:CGPA|GPA))",
    re.I,
)
BULLET_RE = re.compile(r"^(?:[•●▪◦‣■□◆◇►▸➤➤*]|\-|\–|\—)\s*")

# Job / project entry headers: Title | Org ... dates
PIPE_HEADER_RE = re.compile(r".+\|.+")


def structure_resume_text(raw_text: str) -> dict[str, Any]:
    text = _normalize_text(raw_text)
    segments = segment_resume_text(text)

    header_lines = section_lines(segments, "header")
    contact = _extract_contact(header_lines, text)
    headline = _guess_headline(header_lines, contact.get("name"))

    summary = _join_paragraph(section_lines(segments, "summary"))
    experience = _parse_experience(section_lines(segments, "experience"))
    projects = _parse_projects(section_lines(segments, "projects"))
    education = _parse_education(section_lines(segments, "education"))
    skills, skill_groups = _parse_skills(section_lines(segments, "skills"))
    certifications = _parse_certifications(section_lines(segments, "certifications"))
    awards = _parse_awards(section_lines(segments, "awards"))
    languages = _parse_skill_list_line(" ".join(section_lines(segments, "languages")))
    # Keep skill-group "Languages: Python…" in skills (programming). Spoken langs only
    # come from a dedicated Languages section.
    prog = skill_groups.pop("languages", None)
    if prog:
        for item in prog:
            if item not in skills:
                skills.append(item)

    personal: dict[str, Any] = {"job_title": headline}
    if skill_groups:
        personal["notes"] = None  # keep schema clean; groups flattened into skills

    return normalize_resume_content(
        {
            "schema_version": SCHEMA_VERSION,
            "contact": contact,
            "headline": headline,
            "summary": summary,
            "experience": experience,
            "education": education,
            "skills": skills,
            "projects": projects,
            "certifications": certifications,
            "awards": awards,
            "languages": languages,
            "hobbies": [],
            "personal": personal,
            "links": contact.get("links", []),
        }
    )


def _normalize_text(raw_text: str) -> str:
    text = (raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    # Soft-join hyphenated line wraps: "TypeScript,\nSupabase" stays; but
    # rejoin lines that are clearly mid-sentence continuations later per section.
    lines: list[str] = []
    for line in text.split("\n"):
        cleaned = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(cleaned)
    return "\n".join(lines)


def _reflow_section_lines(lines: list[str]) -> list[str]:
    """Merge wrapped PDF lines into logical resume lines."""
    if not lines:
        return []
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if detect_section_name(stripped) and not split_is_inline_content(stripped):
            continue
        if _is_new_logical_line(stripped) or not out:
            out.append(stripped)
            continue
        # Continuation of previous line (wrapped bullet / long sentence).
        prev = out[-1]
        if BULLET_RE.match(prev) or not _is_new_logical_line(stripped):
            joiner = "" if prev.endswith("-") else " "
            out[-1] = f"{prev}{joiner}{stripped}"
        else:
            out.append(stripped)
    return out


def split_is_inline_content(line: str) -> bool:
    """True when heading has trailing content on the same line."""
    from careerpilot.domains.resume.parser.sections import split_heading_remainder

    section, rest = split_heading_remainder(line)
    return bool(section and rest)


def _is_new_logical_line(line: str) -> bool:
    if BULLET_RE.match(line):
        return True
    if detect_section_name(line):
        return True
    # Skill group rows: "Data Engineering: BigQuery, …"
    if re.match(r"^[A-Za-z][A-Za-z0-9 &/+\-]{1,40}:\s*\S", line):
        return True
    if PIPE_HEADER_RE.match(line) and (
        DATE_RANGE_RE.search(line) or SINGLE_DATE_RE.search(line)
    ):
        return True
    if DATE_RANGE_RE.search(line) and "|" in line:
        return True
    # Short non-bullet header-like lines
    if len(line.split()) <= 12 and not line.endswith(",") and not line[0].islower():
        if DATE_RANGE_RE.search(line) or "|" in line:
            return True
    return False


def _extract_contact(header_lines: list[str], raw_text: str) -> dict[str, Any]:
    email_match = EMAIL_RE.search(raw_text)
    phone_match = PHONE_RE.search(raw_text)
    links = list(dict.fromkeys(URL_RE.findall(raw_text)))[:10]

    name = None
    for line in header_lines[:5]:
        if EMAIL_RE.search(line) or PHONE_RE.search(line) or URL_RE.search(line):
            continue
        if detect_section_name(line):
            break
        if "|" in line:
            continue
        if 2 <= len(line.split()) <= 6 and not line.endswith(":"):
            name = line
            break

    location = None
    # Prefer pipe-delimited contact row: phone | email | location | linkedin
    for line in header_lines:
        if "|" not in line:
            continue
        if not (EMAIL_RE.search(line) or PHONE_RE.search(line) or URL_RE.search(line)):
            continue
        parts = [p.strip() for p in line.split("|")]
        for part in parts:
            if EMAIL_RE.search(part) or PHONE_RE.search(part) or URL_RE.search(part):
                continue
            if 1 <= len(part.split()) <= 6 and not re.search(r"\d{4}", part):
                location = part
                break
        if location:
            break

    return {
        "name": name,
        "email": email_match.group(0) if email_match else None,
        "phone": _clean_phone(phone_match.group(0)) if phone_match else None,
        "location": location,
        "links": links,
    }


def _clean_phone(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _guess_headline(header_lines: list[str], name: str | None) -> str | None:
    for line in header_lines[:12]:
        if name and line == name:
            continue
        if EMAIL_RE.search(line) or PHONE_RE.search(line) or URL_RE.search(line):
            continue
        if "|" in line:
            continue
        if detect_section_name(line):
            break
        if 1 <= len(line.split()) <= 10:
            return line
    return None


def _join_paragraph(lines: list[str]) -> str | None:
    lines = _reflow_section_lines(lines)
    if not lines:
        return None
    return " ".join(lines).strip() or None


def _parse_experience(lines: list[str]) -> list[dict[str, Any]]:
    lines = _reflow_section_lines(lines)
    blocks = _split_role_blocks(lines)
    experience: list[dict[str, Any]] = []
    for index, block in enumerate(blocks, start=1):
        if not block:
            continue
        header = block[0]
        title, company, location, start, end, is_current = _parse_role_header(header)
        # Optional second line company if header was title-only
        body_start = 1
        if not company and len(block) > 1 and not BULLET_RE.match(block[1]):
            maybe = block[1]
            if not DATE_RANGE_RE.search(maybe) or "|" not in maybe:
                company = maybe
                body_start = 2
                dates = DATE_RANGE_RE.search(maybe)
                if dates:
                    start = start or dates.group(1)
                    end = end or dates.group(2)
                    if end and end.lower() in {"present", "current", "now"}:
                        is_current = True
                        end = None
        bullets = _collect_bullets(block[body_start:])
        if not title and not company and not bullets:
            continue
        experience.append(
            {
                "id": f"experience_{index:02d}",
                "title": title,
                "company": company,
                "location": location,
                "start_date": start,
                "end_date": None if is_current else end,
                "is_current": is_current,
                "summary": None,
                "bullets": bullets,
                "source_fact_ids": [],
            }
        )
    return experience


def _parse_projects(lines: list[str]) -> list[dict[str, Any]]:
    lines = _reflow_section_lines(lines)
    blocks = _split_role_blocks(lines)
    projects: list[dict[str, Any]] = []
    for index, block in enumerate(blocks, start=1):
        if not block:
            continue
        header = block[0]
        title, organization, _loc, start, end, is_current = _parse_role_header(header)
        # "Tracky | Personal Production Analytics Platform" → title/org
        bullets = _collect_bullets(block[1:])
        if not title and not bullets:
            continue
        projects.append(
            {
                "id": f"project_{index:02d}",
                "title": title,
                "organization": organization,
                "start_date": start,
                "end_date": None if is_current else end,
                "is_current": is_current,
                "summary": None,
                "bullets": bullets,
                "technologies": [],
                "source_fact_ids": [],
            }
        )
    return projects


def _parse_role_header(header: str) -> tuple[
    str | None, str | None, str | None, str | None, str | None, bool
]:
    """
    Parse headers like:
      Associate Software Engineer | Epsilon, Bangalore FEB 2024 – PRESENT
      Tracky | Personal Production Analytics Platform FEB 2024 – PRESENT
      Frontend Developer Intern | Technotharanga Solutions Pvt. Ltd. , Tumkur OCT 2022 – FEB 2023
    """
    line = header.strip()
    start = end = None
    is_current = False
    trailing = TRAILING_DATE_RE.search(line)
    if trailing:
        start, end = trailing.group(1), trailing.group(2)
        line = line[: trailing.start()].strip(" |·•-–—")
        if end.lower() in {"present", "current", "now"}:
            is_current = True
            end = None
    else:
        dates = DATE_RANGE_RE.search(line)
        if dates:
            start, end = dates.group(1), dates.group(2)
            line = DATE_RANGE_RE.sub("", line).strip(" |·•-–—")
            if end.lower() in {"present", "current", "now"}:
                is_current = True
                end = None

    title = company = location = None
    if "|" in line:
        left, right = line.split("|", 1)
        title = left.strip(" |-–—") or None
        right = right.strip(" |-–—")
        # Company, Location  OR  subtitle/org
        if "," in right:
            # Prefer last comma-separated token as location when short
            parts = [p.strip() for p in right.split(",") if p.strip()]
            if len(parts) >= 2 and len(parts[-1].split()) <= 4:
                location = parts[-1]
                company = ", ".join(parts[:-1])
            else:
                company = right
        else:
            company = right or None
    elif " at " in line.lower():
        left, right = re.split(r"\s+at\s+", line, maxsplit=1, flags=re.I)
        title, company = left.strip() or None, right.strip() or None
    else:
        title = line or None

    return title, company, location, start, end, is_current


def _split_role_blocks(lines: list[str]) -> list[list[str]]:
    """
    Inside Experience/Projects: a new entry starts when a non-bullet line looks like
    a role header (pipe + dates, or Title|Org, or date range).
    """
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if _is_role_header(line) and current:
            blocks.append(current)
            current = [line]
            continue
        current.append(line)
    if current:
        blocks.append(current)
    return blocks


def _is_role_header(line: str) -> bool:
    if BULLET_RE.match(line):
        return False
    if DATE_RANGE_RE.search(line) and ("|" in line or len(line.split()) <= 16):
        return True
    if "|" in line and not line.lower().startswith(("data engineering", "cloud", "ai:")):
        # Education-like or project/job header
        return True
    return False


def _collect_bullets(lines: list[str]) -> list[str]:
    bullets: list[str] = []
    for line in lines:
        text = BULLET_RE.sub("", line).strip()
        if not text:
            continue
        if BULLET_RE.match(line) or not bullets:
            if BULLET_RE.match(line):
                bullets.append(text)
            elif not _is_role_header(line):
                # Non-bullet prose under a role — treat as summary bullet
                bullets.append(text)
            continue
        # Continuation without bullet marker
        if not _is_role_header(line) and bullets:
            bullets[-1] = f"{bullets[-1]} {text}".strip()
        elif not _is_role_header(line):
            bullets.append(text)
    # Drop tiny garbage fragments from bad PDF wraps
    cleaned = []
    for b in bullets:
        if len(b) <= 2:
            continue
        if re.fullmatch(r"[a-z]+", b) and len(b) < 12:
            if cleaned:
                cleaned[-1] = f"{cleaned[-1]} {b}"
            continue
        cleaned.append(b)
    return cleaned


def _parse_education(lines: list[str]) -> list[dict[str, Any]]:
    lines = _reflow_section_lines(lines)
    # Also split mashed single-line multi-degrees
    expanded: list[str] = []
    for line in lines:
        expanded.extend(_split_education_line(line))
    education: list[dict[str, Any]] = []
    for index, line in enumerate(expanded, start=1):
        degree, institution, location, end_date, score, score_type = _parse_education_line(line)
        if not degree and not institution:
            continue
        education.append(
            {
                "id": f"education_{index:02d}",
                "degree": degree,
                "institution": institution,
                "location": location,
                "start_date": None,
                "end_date": end_date,
                "is_current": False,
                "score": score,
                "score_type": score_type,
                "summary": None,
                "details": [],
                "source_fact_ids": [],
            }
        )
    return education


def _split_education_line(line: str) -> list[str]:
    """Split 'MCA | School Sep 2024 | 8.75 CGPA Bachelor …' into two records when needed."""
    # Look for a second degree keyword after the first CGPA/date cluster.
    pattern = re.compile(
        r"(?=(?:Master|Bachelor|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|Ph\.?D\.?|"
        r"BCA|MCA|B\.?Tech|M\.?Tech)\b)",
        re.I,
    )
    parts = [p.strip(" |") for p in pattern.split(line) if p and p.strip(" |")]
    # pattern.split with lookahead can leave leading empty; also may not split.
    if len(parts) <= 1:
        # Try split on CGPA boundary: "8.75 CGPA Bachelor"
        alt = re.split(r"(?<=\bCGPA)\s+(?=[A-Z])", line)
        if len(alt) > 1:
            return [p.strip(" |") for p in alt if p.strip(" |")]
        return [line]
    # Re-attach degree keyword: split() with lookahead keeps delimiter in following part
    # Actually with (?=...) the delimiter stays with the following segment — good.
    return parts if parts[0][0:1].isupper() or parts[0].lower().startswith(
        ("master", "bachelor", "bca", "mca")
    ) else [line]


def _parse_education_line(
    line: str,
) -> tuple[str | None, str | None, str | None, str | None, str | None, str | None]:
    score = None
    score_type = None
    cgpa = CGPA_RE.search(line)
    if cgpa:
        score = cgpa.group(1) or cgpa.group(2)
        score_type = "cgpa" if "cgpa" in cgpa.group(0).lower() else "gpa"
        line = CGPA_RE.sub("", line).strip(" |")

    end_date = None
    # Prefer dates near the end
    dates = list(SINGLE_DATE_RE.finditer(line))
    if dates:
        end_date = dates[-1].group(1)
        # Remove only that trailing date occurrence
        start_i, end_i = dates[-1].span()
        line = (line[:start_i] + line[end_i:]).strip(" |")

    degree = institution = location = None
    if "|" in line:
        left, right = line.split("|", 1)
        degree = left.strip(" |") or None
        right = right.strip(" |")
        if "," in right:
            parts = [p.strip() for p in right.split(",") if p.strip()]
            if len(parts) >= 2 and len(parts[-1].split()) <= 4:
                location = parts[-1]
                institution = ", ".join(parts[:-1])
            else:
                institution = right
        else:
            institution = right or None
    else:
        degree = line or None

    return degree, institution, location, end_date, score, score_type


def _parse_skills(lines: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    lines = _reflow_section_lines(lines)
    groups: dict[str, list[str]] = {}
    flat: list[str] = []

    category_split = re.compile(
        r"(?=\b(?:Data Engineering|Cloud\s*&\s*DevOps|Cloud and DevOps|AI|Languages?|"
        r"Programming Languages?|Programming)\s*:)",
        re.I,
    )

    for raw in lines:
        for chunk in category_split.split(raw):
            chunk = chunk.strip()
            if not chunk:
                continue
            if ":" in chunk:
                label, rest = chunk.split(":", 1)
                key = _skill_group_key(label)
                items = _parse_skill_list_line(rest)
                if key:
                    groups.setdefault(key, [])
                    for item in items:
                        if item not in groups[key]:
                            groups[key].append(item)
                        if item not in flat:
                            flat.append(item)
                else:
                    for item in items:
                        if item not in flat:
                            flat.append(item)
            else:
                for item in _parse_skill_list_line(chunk):
                    if item not in flat:
                        flat.append(item)
    return flat, groups


def _skill_group_key(label: str) -> str | None:
    cleaned = re.sub(r"[^a-zA-Z0-9 &]+", "", label).strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    mapping = {
        "data engineering": "data_engineering",
        "cloud devops": "cloud_devops",
        "cloud & devops": "cloud_devops",
        "cloud and devops": "cloud_devops",
        "ai": "ai",
        "languages": "languages",
        "language": "languages",
        "programming languages": "languages",
        "programming": "languages",
    }
    return mapping.get(cleaned)


def _parse_skill_list_line(text: str) -> list[str]:
    # Keep CI/CD, ETL/ELT intact — do not split on '/'.
    parts = re.split(r"[,|•;]", text)
    out: list[str] = []
    for part in parts:
        skill = part.strip(" -•*")
        if not skill:
            continue
        if skill.lower() in {"and", "or"}:
            continue
        if detect_section_name(skill):
            continue
        if len(skill) > 60:
            continue
        if len(skill.split()) > 6:
            continue
        out.append(skill)
    return list(dict.fromkeys(out))


def _parse_certifications(lines: list[str]) -> list[dict[str, Any]]:
    lines = _reflow_section_lines(lines)
    blob = " | ".join(lines)
    # Split on | or • 
    parts = re.split(r"[|•]", blob)
    certs: list[dict[str, Any]] = []
    for index, part in enumerate(parts, start=1):
        title = part.strip(" -•*")
        if not title or len(title) < 3:
            continue
        if detect_section_name(title):
            continue
        certs.append(
            {
                "id": f"certification_{index:02d}",
                "title": title,
                "issuer": None,
                "date": None,
                "expiry_date": None,
                "credential_id": None,
                "url": None,
                "summary": None,
                "source_fact_ids": [],
            }
        )
    return certs


def _parse_awards(lines: list[str]) -> list[dict[str, Any]]:
    lines = _reflow_section_lines(lines)
    awards: list[dict[str, Any]] = []
    for index, line in enumerate(lines, start=1):
        title = BULLET_RE.sub("", line).strip()
        if not title:
            continue
        awards.append(
            {
                "id": f"award_{index:02d}",
                "title": title,
                "issuer": None,
                "date": None,
                "summary": None,
                "source_fact_ids": [],
            }
        )
    return awards
