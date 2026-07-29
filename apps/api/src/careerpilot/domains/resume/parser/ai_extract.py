"""AI-assisted resume structuring (section-aware, validated, OpenAI-compatible).

Pipeline:
  clean text → section detection → structured extraction → validation →
  optional verification pass → map to CareerPilot schema → source_fact_ids
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from careerpilot.config import settings
from careerpilot.domains.resume.parser.sections import (
    format_sections_for_prompt,
    segment_resume_text,
)
from careerpilot.domains.resume.schema import normalize_resume_content

logger = logging.getLogger(__name__)

PARSER_VERSION = "ai_v3"

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

RESUME_PARSER_SYSTEM_PROMPT = """
You are an expert Resume Parsing Engine.

Your task is to extract structured information from a resume into the provided JSON schema.

This is NOT a summarization task.
This is NOT a resume rewriting task.
Your goal is to preserve the original information as faithfully as possible.

############################################################
PRIMARY OBJECTIVE
############################################################

Extract information exactly as written in the resume.
Never improve wording.
Never paraphrase.
Never rewrite.
Never infer.
Never hallucinate.
Never invent missing values.
If information is missing, return null or an empty array.

############################################################
GENERAL RULES
############################################################

1. Return ONLY valid JSON.
2. Do not output markdown.
3. Do not explain your reasoning.
4. Preserve original capitalization.
5. Preserve original dates.
6. Preserve original numbers.
7. Preserve original company names.
8. Preserve original certification names.
9. Preserve original bullet wording.
10. Do not merge sections.

The user message may include a pre-detected SECTION map. Prefer those boundaries.
If a section is empty in the map, leave the corresponding JSON arrays/fields empty/null.

############################################################
SECTION DETECTION
############################################################

Recognize these sections:
HEADER, PROFESSIONAL OVERVIEW, SUMMARY, PROFILE, WORK EXPERIENCE, EXPERIENCE,
EMPLOYMENT, PROJECTS, EDUCATION, SKILLS, CERTIFICATIONS, LICENSES, AWARDS,
PUBLICATIONS, LANGUAGES, HOBBIES, INTERESTS.

A section ends immediately when another section heading begins.
Never extract information across section boundaries.

############################################################
HEADER
############################################################

Extract: Name, Headline, Email, Phone, Location, Portfolio, LinkedIn, GitHub, Website.
Do not extract skills into the header.

############################################################
SUMMARY
############################################################

Extract ONLY the professional summary / professional overview.
Do not rewrite. Do not shorten. Do not improve grammar. Copy exactly.
Stop immediately when the Skills or Experience section begins.

############################################################
WORK EXPERIENCE
############################################################

Only parse information inside the WORK EXPERIENCE / EXPERIENCE / EMPLOYMENT section.

A new experience starts when one of these patterns appears:
  <Job Title> | <Company>
  <Job Title>
  <Company>
  <Job Title> followed by a date range.

Everything until the next job belongs to that experience.

Each experience must contain: company, title (job_title), location, start_date,
end_date, currently_working, summary, achievements (bullets).

Rules:
- Company must NEVER contain bullet points.
- Job title must NEVER contain bullet points.
- Bullet points must NEVER become company names or job titles.
- Never merge two jobs. Never split one job into multiple jobs.
- If Present exists: currently_working=true and end_date=null.
- If dates are missing: leave them null.

Example:
  Associate Software Engineer | Epsilon, Bangalore FEB 2024 – PRESENT
→ job_title=Associate Software Engineer, company=Epsilon, location=Bangalore,
  start_date=FEB 2024, currently_working=true, end_date=null

############################################################
PROJECTS
############################################################

Only parse inside the PROJECTS section.
Each project starts with a project title.
If a title contains a date, SPLIT the date out — do not keep dates inside titles.

Example:
  Tracky | Personal Analytics Platform FEB 2024 – PRESENT
→ title=Tracky | Personal Analytics Platform
  start_date=FEB 2024
  end_date=null
  currently_working=true

############################################################
EDUCATION
############################################################

Only parse inside the EDUCATION section.
Each education record: degree, institution, location, end_date (graduation_date), cgpa.
Do not infer missing start dates. Do not guess durations.
Never place Skills into Education.

############################################################
SKILLS
############################################################

Extract only professional / technical skills.
Ignore sentences. Split comma-separated values.
Categorize where possible into skill_groups keys such as:
  programming_languages, frameworks, databases, cloud, data_engineering, ai, devops, tools
Also return a flat "skills" array of all technology names.
Programming languages (Python, SQL, JavaScript, TypeScript) belong in skills / skill_groups —
NOT in the spoken "languages" array.
Remove duplicates. Never return paragraphs. Never include section headers.

############################################################
LANGUAGES (spoken)
############################################################

"languages" means spoken human languages only (English, French, German, Hindi, Kannada).
Do NOT include Python, SQL, JavaScript, TypeScript — those belong in skills.
If no spoken languages exist, return [].

############################################################
CERTIFICATIONS
############################################################

Only parse inside Certifications / Licenses.
Split certifications separated by | or • or ,
Each: name, issuer, issue_date, expiry_date, credential_id, credential_url
Never invent issuers. Never invent dates.

############################################################
LINKS
############################################################

Extract LinkedIn, GitHub, Portfolio, Website. Deduplicate.

############################################################
ANTI-HALLUCINATION RULES
############################################################

Do NOT rewrite summaries, achievements, projects, or certification names.
Do NOT change company names, numbers, percentages, dates, or technologies.

Resume says 2–10TB+ → output MUST be 2–10TB+ (NOT 2–20TB+)
Resume says BigQuery → output MUST be BigQuery (NOT Google BigQuery)

############################################################
TEXT NORMALIZATION
############################################################

Fix only obvious OCR / encoding issues (e.g. Typedcript→TypeScript).
Trim whitespace. Remove duplicated spaces.
Remove invalid Unicode replacement characters.
Do NOT change wording beyond that.

############################################################
VALIDATION
############################################################

Before returning JSON validate everything:
- Experience: company and title non-empty when possible; bullets are arrays;
  company/title contain no bullets
- Projects: title contains no dates; dates stored separately
- Education: not inside Projects; Skills not inside Education
- Skills: no paragraphs; no duplicates
- Languages: spoken languages only
- Certifications: unique; no inferred dates
- Header: email/phone valid when present; links deduplicated
If validation fails, repair the JSON before returning.

############################################################
CONFIDENCE (OPTIONAL)
############################################################

You may attach confidence as a sibling field ending in _confidence (0.0–1.0),
e.g. "company": "Epsilon", "company_confidence": 0.99
Prefer flat string/array values for all schema fields.
Do NOT wrap values as {"value": "...", "confidence": 0.9} unless unavoidable —
if you do, the backend will unwrap .value.

Low confidence (<0.80) means the field should be reviewed by the user.

############################################################
OUTPUT
############################################################

Return ONLY valid JSON matching the schema below.
Do not omit arrays. Unknown values must be null. No explanations.

SCHEMA:
{
  "full_name": null,
  "headline": null,
  "email": null,
  "phone": null,
  "location": null,
  "linkedin": null,
  "github": null,
  "portfolio": null,
  "website": null,
  "summary": null,
  "skills": [],
  "skill_groups": {
    "programming_languages": [],
    "data_engineering": [],
    "cloud": [],
    "ai": [],
    "devops": [],
    "tools": []
  },
  "experience": [
    {
      "job_title": null,
      "company": null,
      "location": null,
      "start_date": null,
      "end_date": null,
      "currently_working": false,
      "summary": null,
      "achievements": []
    }
  ],
  "education": [
    {
      "degree": null,
      "institution": null,
      "location": null,
      "start_date": null,
      "end_date": null,
      "grade": null,
      "cgpa": null,
      "specialization": null
    }
  ],
  "projects": [
    {
      "title": null,
      "organization": null,
      "location": null,
      "start_date": null,
      "end_date": null,
      "currently_working": false,
      "summary": null,
      "highlights": [],
      "technologies": []
    }
  ],
  "certifications": [
    {
      "name": null,
      "issuer": null,
      "issue_date": null,
      "expiry_date": null,
      "credential_id": null,
      "credential_url": null
    }
  ],
  "awards": [
    {
      "title": null,
      "issuer": null,
      "date": null,
      "summary": null
    }
  ],
  "languages": []
}
""".strip()




AI_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "full_name": {"type": ["string", "null"]},
        "headline": {"type": ["string", "null"]},
        "email": {"type": ["string", "null"]},
        "phone": {"type": ["string", "null"]},
        "location": {"type": ["string", "null"]},
        "linkedin": {"type": ["string", "null"]},
        "github": {"type": ["string", "null"]},
        "portfolio": {"type": ["string", "null"]},
        "website": {"type": ["string", "null"]},
        "summary": {"type": ["string", "null"]},
        "skills": {"type": "array", "items": {"type": "string"}},
        "skill_groups": {
            "type": "object",
            "additionalProperties": {"type": "array", "items": {"type": "string"}},
        },
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "job_title": {"type": ["string", "null"]},
                    "company": {"type": ["string", "null"]},
                    "location": {"type": ["string", "null"]},
                    "start_date": {"type": ["string", "null"]},
                    "end_date": {"type": ["string", "null"]},
                    "currently_working": {"type": "boolean"},
                    "summary": {"type": ["string", "null"]},
                    "achievements": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "job_title",
                    "company",
                    "location",
                    "start_date",
                    "end_date",
                    "currently_working",
                    "summary",
                    "achievements",
                ],
            },
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "degree": {"type": ["string", "null"]},
                    "institution": {"type": ["string", "null"]},
                    "location": {"type": ["string", "null"]},
                    "start_date": {"type": ["string", "null"]},
                    "end_date": {"type": ["string", "null"]},
                    "grade": {"type": ["string", "null"]},
                    "cgpa": {"type": ["string", "null"]},
                    "specialization": {"type": ["string", "null"]},
                },
                "required": [
                    "degree",
                    "institution",
                    "location",
                    "start_date",
                    "end_date",
                    "grade",
                    "cgpa",
                    "specialization",
                ],
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": ["string", "null"]},
                    "organization": {"type": ["string", "null"]},
                    "location": {"type": ["string", "null"]},
                    "start_date": {"type": ["string", "null"]},
                    "end_date": {"type": ["string", "null"]},
                    "currently_working": {"type": "boolean"},
                    "summary": {"type": ["string", "null"]},
                    "highlights": {"type": "array", "items": {"type": "string"}},
                    "technologies": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "title",
                    "organization",
                    "location",
                    "start_date",
                    "end_date",
                    "currently_working",
                    "summary",
                    "highlights",
                    "technologies",
                ],
            },
        },
        "certifications": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": ["string", "null"]},
                    "issuer": {"type": ["string", "null"]},
                    "issue_date": {"type": ["string", "null"]},
                    "expiry_date": {"type": ["string", "null"]},
                    "credential_id": {"type": ["string", "null"]},
                    "credential_url": {"type": ["string", "null"]},
                },
                "required": [
                    "name",
                    "issuer",
                    "issue_date",
                    "expiry_date",
                    "credential_id",
                    "credential_url",
                ],
            },
        },
        "awards": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": ["string", "null"]},
                    "issuer": {"type": ["string", "null"]},
                    "date": {"type": ["string", "null"]},
                    "summary": {"type": ["string", "null"]},
                },
                "required": ["title", "issuer", "date", "summary"],
            },
        },
        "languages": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "full_name",
        "headline",
        "email",
        "phone",
        "location",
        "linkedin",
        "github",
        "portfolio",
        "website",
        "summary",
        "skills",
        "skill_groups",
        "experience",
        "education",
        "projects",
        "certifications",
        "awards",
        "languages",
    ],
}


class AIParseError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def ai_resume_parsing_enabled() -> bool:
    return bool(settings.resume_ai_enabled and settings.resume_ai_api_base.strip())


# ---------------------------------------------------------------------------
# Deterministic validation / repair
# ---------------------------------------------------------------------------

_SECTION_LEAK_RE = re.compile(
    r"\b(skills?|education|projects?|certifications?|awards?|experience|summary)\b",
    re.I,
)
_BULLET_MARK_RE = re.compile(r"[•●▪◦‣■□◆◇►▸➤➤]|^\s*[-*]\s+")
_ACTION_VERB_RE = re.compile(
    r"\b(designed|built|developed|implemented|created|led|managed|optimized|"
    r"architected|deployed|automated|improved|reduced|increased)\b",
    re.I,
)


_PROGRAMMING_LANG_RE = re.compile(
    r"^(python|sql|javascript|typescript|java|c\+\+|c#|go|golang|rust|ruby|php|"
    r"scala|kotlin|swift|r|matlab|bash|shell|powershell)$",
    re.I,
)
_SPOKEN_LANG_HINTS = {
    "english",
    "french",
    "german",
    "hindi",
    "kannada",
    "tamil",
    "telugu",
    "spanish",
    "mandarin",
    "chinese",
    "japanese",
    "korean",
    "arabic",
    "portuguese",
    "italian",
    "russian",
    "bengali",
    "marathi",
    "urdu",
}


def validate_and_repair_ai_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Apply ATS-style rejection/repair rules to model JSON before mapping."""
    out = _unwrap_confidence_tree(dict(raw))

    skills = _as_str_list(out.get("skills"))
    # Flatten skill_groups into skills when present.
    groups = out.get("skill_groups")
    if isinstance(groups, dict):
        for items in groups.values():
            skills.extend(_as_str_list(items))
    out["skills"] = list(
        dict.fromkeys(
            s for s in skills if 0 < len(s.split()) <= 5 and not _SECTION_LEAK_RE.fullmatch(s)
        )
    )

    languages = _as_str_list(out.get("languages"))
    out["languages"] = [
        s
        for s in languages
        if 0 < len(s.split()) <= 3
        and not _PROGRAMMING_LANG_RE.match(s)
        and (s.lower() in _SPOKEN_LANG_HINTS or len(s.split()) <= 2)
    ]
    # Move accidental programming langs from languages → skills
    for s in languages:
        if _PROGRAMMING_LANG_RE.match(s) and s not in out["skills"]:
            out["skills"].append(s)

    experience: list[dict[str, Any]] = []
    for item in _as_list(out.get("experience")):
        if not isinstance(item, dict):
            continue
        title = _as_str(item.get("job_title") or item.get("title"))
        company = _as_str(item.get("company"))
        if not title and not company:
            continue
        if title and (_BULLET_MARK_RE.search(title) or _SECTION_LEAK_RE.search(title)):
            continue
        if company and (
            _BULLET_MARK_RE.search(company)
            or _ACTION_VERB_RE.search(company)
            or _SECTION_LEAK_RE.search(company)
        ):
            # Likely a leaked bullet — drop the row rather than pollute company.
            continue
        achievements = _as_str_list(item.get("achievements") or item.get("bullets"))
        achievements = [a for a in achievements if a and not _SECTION_LEAK_RE.fullmatch(a)]
        end_date = _as_str(item.get("end_date"))
        currently = bool(item.get("currently_working") or item.get("is_current"))
        if end_date and end_date.lower() in {"present", "current", "now"}:
            currently = True
            end_date = None
        experience.append(
            {
                **item,
                "job_title": title,
                "company": company,
                "end_date": end_date,
                "currently_working": currently,
                "achievements": achievements,
            }
        )
    out["experience"] = _dedupe_dicts(experience, keys=("job_title", "company", "start_date"))

    projects: list[dict[str, Any]] = []
    for item in _as_list(out.get("projects")):
        if not isinstance(item, dict):
            continue
        title = _as_str(item.get("title") or item.get("name"))
        if not title:
            continue
        if title.upper().startswith(("EDUCATION", "CERTIFICATION", "SKILLS", "AWARDS", "EXPERIENCE")):
            continue
        if _BULLET_MARK_RE.search(title) or _SECTION_LEAK_RE.fullmatch(title):
            continue
        # Strip trailing date ranges from project titles.
        date_match = re.search(
            r"\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4})"
            r"\s*[-–—to]+\s*"
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4}|Present|Current|Now)\s*$",
            title,
            re.I,
        )
        start_date = _as_str(item.get("start_date"))
        end_date = _as_str(item.get("end_date"))
        currently = bool(item.get("currently_working") or item.get("is_current"))
        if date_match:
            title = title[: date_match.start()].strip(" |·•-–—")
            start_date = start_date or date_match.group(1)
            end_raw = date_match.group(2)
            if end_raw.lower() in {"present", "current", "now"}:
                currently = True
                end_date = None
            else:
                end_date = end_date or end_raw
        highlights = _as_str_list(item.get("highlights") or item.get("bullets"))
        technologies = [t for t in _as_str_list(item.get("technologies")) if len(t.split()) <= 5]
        projects.append(
            {
                **item,
                "title": title,
                "start_date": start_date,
                "end_date": end_date,
                "currently_working": currently,
                "highlights": highlights,
                "technologies": technologies,
            }
        )
    out["projects"] = _dedupe_dicts(projects, keys=("title", "organization", "start_date"))

    education: list[dict[str, Any]] = []
    for item in _as_list(out.get("education")):
        if not isinstance(item, dict):
            continue
        institution = _as_str(item.get("institution") or item.get("school"))
        degree = _as_str(item.get("degree"))
        if not institution and not degree:
            continue
        if institution and _BULLET_MARK_RE.search(institution):
            continue
        education.append(item)
    out["education"] = _dedupe_dicts(education, keys=("institution", "degree", "end_date"))

    certifications: list[dict[str, Any]] = []
    for item in _as_list(out.get("certifications")):
        if not isinstance(item, dict):
            continue
        name = _as_str(item.get("name") or item.get("title"))
        if not name:
            continue
        if name.upper().startswith(("PROJECT", "EDUCATION", "SKILLS")):
            continue
        certifications.append({**item, "name": name})
    out["certifications"] = _dedupe_dicts(certifications, keys=("name", "issuer", "issue_date"))

    awards: list[dict[str, Any]] = []
    for item in _as_list(out.get("awards")):
        if not isinstance(item, dict):
            continue
        title = _as_str(item.get("title") or item.get("name"))
        if not title:
            continue
        awards.append({**item, "title": title})
    out["awards"] = _dedupe_dicts(awards, keys=("title", "issuer", "date"))

    # Summary must not swallow skills/experience headings.
    summary = _as_str(out.get("summary"))
    if summary:
        summary = re.split(
            r"\n\s*(?:skills?|technical skills|experience|work experience|projects?|education)\s*$",
            summary,
            flags=re.I,
        )[0].strip()
        # Drop if it looks like a dumped skills paragraph with no sentence structure.
        if len(summary.split()) > 120 and summary.count(",") > 12:
            summary = summary.split(".")[0].strip() or None
    out["summary"] = summary

    location = _as_str(out.get("location"))
    if location and (
        _ACTION_VERB_RE.search(location)
        or "," in location
        and any(tok.lower() in location.lower() for tok in out["skills"][:8])
        and len(location.split()) > 8
    ):
        # Skills leaked into location — keep only first short place-like chunk.
        if len(location.split()) > 6:
            out["location"] = None

    for key in ("linkedin", "github", "portfolio", "website"):
        out[key] = _as_str(out.get(key))

    return out


def _dedupe_dicts(items: list[dict[str, Any]], *, keys: tuple[str, ...]) -> list[dict[str, Any]]:
    seen: set[tuple[str, ...]] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        signature = tuple((_as_str(item.get(k)) or "").lower() for k in keys)
        if signature in seen and any(signature):
            continue
        seen.add(signature)
        out.append(item)
    return out


def _unwrap_confidence_tree(value: Any) -> Any:
    """Normalize {value, confidence} wrappers (and nested structures) to plain values."""
    if isinstance(value, dict):
        if set(value.keys()) <= {"value", "confidence"} and "value" in value:
            return _unwrap_confidence_tree(value.get("value"))
        return {k: _unwrap_confidence_tree(v) for k, v in value.items() if not k.endswith("_confidence")}
    if isinstance(value, list):
        return [_unwrap_confidence_tree(item) for item in value]
    return value


# ---------------------------------------------------------------------------
# Mapping + source grounding
# ---------------------------------------------------------------------------

def map_ai_resume_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Map model output into CareerPilot shared resume schema."""
    links: list[str] = []
    for key in ("linkedin", "github", "portfolio", "website"):
        value = _as_str(raw.get(key))
        if value:
            links.append(value)
    links = list(dict.fromkeys(links))

    experience = []
    for item in _as_list(raw.get("experience")):
        if not isinstance(item, dict):
            continue
        experience.append(
            {
                "title": _as_str(item.get("job_title") or item.get("title")),
                "company": _as_str(item.get("company")),
                "location": _as_str(item.get("location")),
                "start_date": _as_str(item.get("start_date")),
                "end_date": _as_str(item.get("end_date")),
                "is_current": bool(item.get("currently_working") or item.get("is_current")),
                "summary": _as_str(item.get("summary")),
                "bullets": _as_str_list(item.get("achievements") or item.get("bullets")),
                "source_fact_ids": _as_str_list(item.get("source_fact_ids")),
            }
        )

    education = []
    for item in _as_list(raw.get("education")):
        if not isinstance(item, dict):
            continue
        score = _as_str(item.get("cgpa") or item.get("gpa") or item.get("grade") or item.get("score"))
        score_type = None
        if _as_str(item.get("cgpa")):
            score_type = "cgpa"
        elif _as_str(item.get("gpa")):
            score_type = "gpa"
        elif _as_str(item.get("grade")):
            score_type = "other"
        education.append(
            {
                "institution": _as_str(item.get("institution") or item.get("school")),
                "degree": _as_str(item.get("degree")),
                "specialization": _as_str(item.get("specialization") or item.get("major")),
                "location": _as_str(item.get("location")),
                "start_date": _as_str(item.get("start_date")),
                "end_date": _as_str(item.get("end_date")),
                "is_current": bool(item.get("currently_studying") or item.get("is_current")),
                "score": score,
                "score_type": score_type,
                "summary": _as_str(item.get("summary")),
                "source_fact_ids": _as_str_list(item.get("source_fact_ids")),
            }
        )

    projects = []
    for item in _as_list(raw.get("projects")):
        if not isinstance(item, dict):
            continue
        projects.append(
            {
                "title": _as_str(item.get("title") or item.get("name")),
                "organization": _as_str(item.get("organization") or item.get("company")),
                "url": _as_str(item.get("url") or item.get("link")),
                "location": _as_str(item.get("location")),
                "start_date": _as_str(item.get("start_date")),
                "end_date": _as_str(item.get("end_date")),
                "is_current": bool(item.get("currently_working") or item.get("is_current")),
                "summary": _as_str(item.get("summary")),
                "bullets": _as_str_list(item.get("highlights") or item.get("bullets")),
                "technologies": _as_str_list(item.get("technologies")),
                "source_fact_ids": _as_str_list(item.get("source_fact_ids")),
            }
        )

    certifications = []
    for item in _as_list(raw.get("certifications")):
        if not isinstance(item, dict):
            continue
        certifications.append(
            {
                "title": _as_str(item.get("name") or item.get("title")),
                "issuer": _as_str(item.get("issuer")),
                "date": _as_str(item.get("issue_date") or item.get("date")),
                "expiry_date": _as_str(item.get("expiry_date")),
                "credential_id": _as_str(item.get("credential_id")),
                "url": _as_str(item.get("credential_url") or item.get("url")),
                "summary": _as_str(item.get("summary")),
                "source_fact_ids": _as_str_list(item.get("source_fact_ids")),
            }
        )

    awards = []
    for item in _as_list(raw.get("awards")):
        if not isinstance(item, dict):
            continue
        awards.append(
            {
                "title": _as_str(item.get("title") or item.get("name")),
                "issuer": _as_str(item.get("issuer")),
                "date": _as_str(item.get("date")),
                "summary": _as_str(item.get("summary")),
                "source_fact_ids": _as_str_list(item.get("source_fact_ids")),
            }
        )

    return normalize_resume_content(
        {
            "contact": {
                "name": _as_str(raw.get("full_name") or raw.get("name")),
                "email": _as_str(raw.get("email")),
                "phone": _as_str(raw.get("phone")),
                "location": _as_str(raw.get("location")),
                "links": links,
            },
            "headline": _as_str(raw.get("headline")),
            "summary": _as_str(raw.get("summary")),
            "skills": _as_str_list(raw.get("skills")),
            "languages": _as_str_list(raw.get("languages")),
            "experience": experience,
            "education": education,
            "projects": projects,
            "certifications": certifications,
            "awards": awards,
            "links": links,
            "personal": {"job_title": _as_str(raw.get("headline"))},
        }
    )


def attach_source_fact_ids(content: dict[str, Any], raw_text: str) -> dict[str, Any]:
    """Ground extracted fields to line ids (L001, L002, …) from the source text."""
    lines = [(n, line.strip()) for n, line in enumerate((raw_text or "").splitlines(), start=1) if line.strip()]
    if not lines:
        return content

    def find_ids(*needles: str | None, limit: int = 6) -> list[str]:
        ids: list[str] = []
        for needle in needles:
            text = (needle or "").strip()
            if len(text) < 4:
                continue
            needle_l = text.lower()
            for line_no, line in lines:
                line_l = line.lower()
                if needle_l in line_l or (len(needle_l) > 24 and line_l in needle_l):
                    fact = f"L{line_no:03d}"
                    if fact not in ids:
                        ids.append(fact)
                    if len(ids) >= limit:
                        return ids
        return ids

    for exp in content.get("experience") or []:
        if not isinstance(exp, dict):
            continue
        ids = find_ids(exp.get("title"), exp.get("company"), *(exp.get("bullets") or [])[:4])
        if ids:
            exp["source_fact_ids"] = ids

    for edu in content.get("education") or []:
        if not isinstance(edu, dict):
            continue
        ids = find_ids(edu.get("institution"), edu.get("degree"))
        if ids:
            edu["source_fact_ids"] = ids

    for proj in content.get("projects") or []:
        if not isinstance(proj, dict):
            continue
        ids = find_ids(proj.get("title"), proj.get("organization"), *(proj.get("bullets") or [])[:3])
        if ids:
            proj["source_fact_ids"] = ids

    for cert in content.get("certifications") or []:
        if not isinstance(cert, dict):
            continue
        ids = find_ids(cert.get("title"), cert.get("issuer"))
        if ids:
            cert["source_fact_ids"] = ids

    for award in content.get("awards") or []:
        if not isinstance(award, dict):
            continue
        ids = find_ids(award.get("title"), award.get("issuer"))
        if ids:
            award["source_fact_ids"] = ids

    return content


# ---------------------------------------------------------------------------
# LLM orchestration
# ---------------------------------------------------------------------------

async def structure_resume_text_with_ai(raw_text: str) -> dict[str, Any]:
    """Call an OpenAI-compatible model and return normalized CareerPilot resume JSON."""
    if not ai_resume_parsing_enabled():
        raise AIParseError("ai_disabled", "AI resume parsing is not enabled.")

    text = (raw_text or "").strip()
    if not text:
        raise AIParseError("empty_text", "No resume text available for AI parsing.")

    max_chars = max(2000, settings.resume_ai_max_chars)
    if len(text) > max_chars:
        text = text[:max_chars]

    segments = segment_resume_text(text)
    section_block = format_sections_for_prompt(segments)

    # Prefer section map only — avoids doubling prompt size (critical for local models).
    if section_block.strip():
        extract_user = (
            "Extract structured resume JSON from these pre-detected sections.\n"
            "Do not mix content across sections.\n\n"
            f"{section_block}"
        )
    else:
        extract_user = (
            "Extract structured resume JSON from the following resume text.\n"
            "No clear headings were detected — apply section rules carefully.\n\n"
            f"{text}"
        )

    logger.info(
        "AI resume extract starting (chars=%s sections=%s verify=%s schema=%s)",
        len(text),
        list((segments.get("order") or [])),
        settings.resume_ai_verify_pass,
        settings.resume_ai_json_schema,
    )

    parsed = await _chat_json(
        system=RESUME_PARSER_SYSTEM_PROMPT,
        user=extract_user,
    )
    parsed = validate_and_repair_ai_payload(parsed)

    if settings.resume_ai_verify_pass:
        try:
            verify_user = (
                "Pre-detected sections:\n"
                f"{section_block or text[:8000]}\n\n"
                "Extracted JSON to validate and repair:\n"
                f"{json.dumps(parsed, ensure_ascii=False)}"
            )
            verified = await _chat_json(
                system=RESUME_VERIFIER_SYSTEM_PROMPT,
                user=verify_user,
            )
            parsed = validate_and_repair_ai_payload(verified)
        except AIParseError as exc:
            logger.warning("Resume AI verify pass failed; keeping first extraction: %s", exc.message)

    mapped = map_ai_resume_payload(parsed)
    return attach_source_fact_ids(mapped, text)


def _response_format_payload() -> dict[str, Any] | None:
    if settings.resume_ai_json_schema:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "resume_extraction",
                "strict": True,
                "schema": AI_JSON_SCHEMA,
            },
        }
    if settings.resume_ai_json_mode:
        return {"type": "json_object"}
    return None


async def _chat_json(*, system: str, user: str) -> dict[str, Any]:
    api_base = settings.resume_ai_api_base.rstrip("/")
    url = f"{api_base}/chat/completions"
    payload: dict[str, Any] = {
        "model": settings.resume_ai_model,
        "temperature": 0,
        "max_tokens": max(512, settings.resume_ai_max_tokens),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    response_format = _response_format_payload()
    if response_format:
        payload["response_format"] = response_format

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.resume_ai_api_key or 'local'}",
    }
    timeout = httpx.Timeout(
        connect=10.0,
        read=settings.resume_ai_timeout_seconds,
        write=30.0,
        pool=10.0,
    )

    response = await _post_chat(url, headers=headers, payload=payload, timeout=timeout)

    if response.status_code >= 400:
        detail = response.text[:500]
        detail_l = detail.lower()
        # LM Studio: only json_schema|text — json_object is rejected.
        if "json_object" in detail_l or (
            "response_format" in detail_l and "json_schema" in detail_l
        ):
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "resume_extraction",
                    "strict": True,
                    "schema": AI_JSON_SCHEMA,
                },
            }
            response = await _post_chat(url, headers=headers, payload=payload, timeout=timeout)
            detail = response.text[:500]
        elif "response_format" in detail_l or "json_schema" in detail_l:
            payload.pop("response_format", None)
            response = await _post_chat(url, headers=headers, payload=payload, timeout=timeout)
            detail = response.text[:500]
        if response.status_code >= 400:
            raise AIParseError(
                "ai_http_error",
                f"AI endpoint returned {response.status_code}: {detail}",
            )

    try:
        body = response.json()
        message = body["choices"][0]["message"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise AIParseError("ai_bad_response", "AI response missing message content.") from exc

    content = _message_text(message)
    if not content.strip():
        raise AIParseError(
            "ai_empty_content",
            "AI returned empty content (reasoning-only). Increase max_tokens or disable thinking.",
        )
    return _parse_json_content(content)


async def _post_chat(
    url: str,
    *,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: httpx.Timeout,
) -> httpx.Response:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(url, headers=headers, json=payload)
    except httpx.TimeoutException as exc:
        raise AIParseError(
            "ai_timeout",
            f"AI timed out after {settings.resume_ai_timeout_seconds:.0f}s "
            f"({type(exc).__name__}). Try RESUME_AI_VERIFY_PASS=false or a faster model.",
        ) from exc
    except httpx.HTTPError as exc:
        detail = str(exc).strip() or type(exc).__name__
        raise AIParseError("ai_unreachable", f"AI endpoint unreachable: {detail}") from exc


def _message_text(message: Any) -> str:
    """Read assistant text from content and/or reasoning_content (Gemma / reasoning models)."""
    if not isinstance(message, dict):
        return str(message or "")
    content = message.get("content")
    reasoning = message.get("reasoning_content")
    parts: list[str] = []
    if isinstance(content, str) and content.strip():
        parts.append(content)
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
    if not parts and isinstance(reasoning, str) and reasoning.strip():
        # Some local reasoning models put the final JSON only in reasoning_content.
        parts.append(reasoning)
    return "\n".join(parts)


def _parse_json_content(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            raise AIParseError("ai_invalid_json", "AI did not return valid JSON.") from None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise AIParseError("ai_invalid_json", "AI did not return valid JSON.") from exc
    if not isinstance(data, dict):
        raise AIParseError("ai_invalid_json", "AI JSON root must be an object.")
    return data


def _as_str(value: Any) -> str | None:
    if isinstance(value, dict) and "value" in value:
        value = value.get("value")
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "n/a", "na"}:
        return None
    return text


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, str):
        parts = [p.strip() for p in re.split(r"[,;\n]", value) if p.strip()]
        return parts
    out: list[str] = []
    for item in _as_list(value):
        text = _as_str(item)
        if text:
            out.append(text)
    return out
