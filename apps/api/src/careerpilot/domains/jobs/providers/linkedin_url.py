"""Fetch a LinkedIn job from a public job URL (guest HTML endpoints)."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from careerpilot.domains.jobs.providers.base import DiscoveredJob

_JOB_ID_RE = re.compile(
    r"(?:linkedin\.com/(?:jobs/view|jobs/collections/[^/]+/)/|currentJobId=)(\d{6,})",
    re.IGNORECASE,
)
_SKILL_CANDIDATES = (
    "python",
    "java",
    "scala",
    "spark",
    "hadoop",
    "javascript",
    "typescript",
    "react",
    "node",
    "nodejs",
    "aws",
    "azure",
    "gcp",
    "google cloud",
    "google cloud platform",
    "kubernetes",
    "docker",
    "sql",
    "postgresql",
    "oracle",
    "mongodb",
    "nosql",
    "redis",
    "kafka",
    "terraform",
    "ansible",
    "jenkins",
    "ci/cd",
    "etl",
    "elt",
    "data warehouse",
    "big data",
    "machine learning",
    "sparkml",
    "go",
    "golang",
    "rust",
    "c++",
    "c#",
    ".net",
    "django",
    "fastapi",
    "flask",
    "spring",
    "graphql",
    "rest",
    "linux",
    "agile",
    "scrum",
    "pytorch",
    "tensorflow",
    "pandas",
    "numpy",
    "elasticsearch",
    "microservices",
    "system design",
    "alloy db",
    "iac",
)


class LinkedInUrlError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def extract_linkedin_job_id(url: str) -> str:
    text = (url or "").strip()
    if not text:
        raise LinkedInUrlError("invalid_url", "LinkedIn job URL is required.")
    match = _JOB_ID_RE.search(text)
    if match:
        return match.group(1)
    if re.fullmatch(r"\d{6,}", text):
        return text
    raise LinkedInUrlError(
        "invalid_url",
        "Could not find a LinkedIn job id. Paste a URL like "
        "https://www.linkedin.com/jobs/view/4252026496/",
    )


def canonicalize_linkedin_job_url(url: str) -> str:
    """Strip tracking query params; keep a short canonical jobs/view URL."""
    job_id = extract_linkedin_job_id(url)
    return f"https://www.linkedin.com/jobs/view/{job_id}/"


def _strip_html(value: str | None) -> str | None:
    if not value:
        return None
    text = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    text = re.sub(r"</(p|li|h\d|div)>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#39;", "'", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() or None


def _infer_skills(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for skill in sorted(_SKILL_CANDIDATES, key=len, reverse=True):
        if skill in lower and skill not in found:
            # Avoid double-counting short aliases covered by longer phrases
            if any(skill in existing and skill != existing for existing in found):
                continue
            found.append(skill)
    return found[:24]


def _remote_type(location: str | None, description: str | None) -> str | None:
    blob = f"{location or ''} {description or ''}".lower()
    if "remote" in blob:
        return "remote"
    if "hybrid" in blob:
        return "hybrid"
    if location:
        return "onsite"
    return None


def _display_skill(skill: str) -> str:
    aliases = {
        "gcp": "GCP",
        "google cloud": "Google Cloud",
        "google cloud platform": "GCP",
        "sql": "SQL",
        "etl": "ETL",
        "elt": "ELT",
        "ci/cd": "CI/CD",
        "iac": "IaC",
        "nosql": "NoSQL",
        "aws": "AWS",
        "c++": "C++",
        "c#": "C#",
        ".net": ".NET",
        "sparkml": "SparkML",
    }
    if skill in aliases:
        return aliases[skill]
    return skill.title() if skill.islower() else skill


def _first_match(html: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            cleaned = _strip_html(match.group(1))
            if cleaned:
                return cleaned
    return None


def _parse_guest_html(job_id: str, html: str, source_url: str) -> DiscoveredJob | None:
    title = _first_match(
        html,
        [
            r'class="[^"]*top-card-layout__title[^"]*"[^>]*>(.*?)</h2>',
            r'class="[^"]*topcard__title[^"]*"[^>]*>(.*?)</h2>',
            r"<h1[^>]*>(.*?)</h1>",
            r"<title>\s*(?:[^|<]+hiring\s+)?([^|<]+?)\s+in\s+[^|<]+\|\s*LinkedIn\s*</title>",
        ],
    )
    company_name = _first_match(
        html,
        [
            r'class="[^"]*topcard__org-name-link[^"]*"[^>]*>(.*?)</a>',
            r'class="[^"]*topcard__flavor--black-link[^"]*"[^>]*>(.*?)</a>',
            r'<a[^>]*data-tracking-control-name="public_jobs_topcard-org-name"[^>]*>(.*?)</a>',
            r"<title>\s*([^|<]+?)\s+hiring\s+",
        ],
    )
    location = _first_match(
        html,
        [
            r'class="[^"]*topcard__flavor--bullet[^"]*"[^>]*>(.*?)</span>',
            r'class="[^"]*topcard__flavor[^"]*"[^>]*>\s*([^<]+?)\s*</span>',
        ],
    )
    description = _first_match(
        html,
        [
            r'class="[^"]*show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>',
            r'class="[^"]*description__text[^"]*"[^>]*>(.*?)</div>',
            r'class="[^"]*core-section-container__content[^"]*"[^>]*>(.*?)</div>\s*</div>',
        ],
    )

    if not title and not description:
        return None

    title = title or "LinkedIn job"
    company_name = company_name or "Unknown company"
    skills = [_display_skill(s) for s in _infer_skills(f"{title}\n{description or ''}")]
    return DiscoveredJob(
        provider="linkedin",
        external_id=job_id,
        title=title,
        company_name=company_name,
        description=description,
        location=location,
        remote_type=_remote_type(location, description),
        canonical_url=f"https://www.linkedin.com/jobs/view/{job_id}/",
        source_url=source_url,
        requirements={"skills": skills} if skills else {},
        raw_payload={"source": "linkedin_guest_html", "job_id": job_id},
    )


def _parse_json_ld(job_id: str, html: str, source_url: str) -> DiscoveredJob | None:
    for match in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.IGNORECASE | re.DOTALL,
    ):
        raw = match.group(1).strip()
        try:
            payload: Any = json.loads(raw)
        except json.JSONDecodeError:
            continue
        candidates = payload if isinstance(payload, list) else [payload]
        for item in candidates:
            if not isinstance(item, dict):
                continue
            types = item.get("@type")
            type_names = types if isinstance(types, list) else [types]
            if "JobPosting" not in type_names:
                continue
            title = str(item.get("title") or "LinkedIn job").strip()
            org = item.get("hiringOrganization") or {}
            company = org.get("name") if isinstance(org, dict) else None
            description = _strip_html(str(item.get("description") or ""))
            loc = None
            job_loc = item.get("jobLocation")
            if isinstance(job_loc, dict):
                address = job_loc.get("address") or {}
                if isinstance(address, dict):
                    parts = [
                        address.get("addressLocality"),
                        address.get("addressRegion"),
                        address.get("addressCountry"),
                    ]
                    loc = ", ".join(str(p) for p in parts if p)
            elif isinstance(job_loc, list) and job_loc:
                first = job_loc[0]
                if isinstance(first, dict):
                    address = first.get("address") or {}
                    if isinstance(address, dict):
                        loc = address.get("addressLocality")
            skills = [_display_skill(s) for s in _infer_skills(f"{title}\n{description or ''}")]
            return DiscoveredJob(
                provider="linkedin",
                external_id=job_id,
                title=title,
                company_name=str(company or "Unknown company"),
                description=description,
                location=loc,
                remote_type=_remote_type(loc, description),
                canonical_url=f"https://www.linkedin.com/jobs/view/{job_id}/",
                source_url=source_url,
                requirements={"skills": skills} if skills else {},
                raw_payload={"source": "linkedin_json_ld", "job_id": job_id},
            )
    return None


def _parse_og_meta(job_id: str, html: str, source_url: str) -> DiscoveredJob | None:
    og_title = _first_match(html, [r'property="og:title"\s+content="([^"]+)"'])
    og_desc = _first_match(html, [r'property="og:description"\s+content="([^"]+)"'])
    if not og_title:
        return None
    # "Google hiring Cloud Data Engineer in Bengaluru, Karnataka, India | LinkedIn"
    company = None
    title = og_title
    location = None
    hiring = re.match(
        r"(.+?)\s+hiring\s+(.+?)\s+in\s+(.+?)(?:\s*\|\s*LinkedIn)?$",
        og_title,
        re.IGNORECASE,
    )
    if hiring:
        company, title, location = hiring.group(1), hiring.group(2), hiring.group(3)
    description = og_desc
    skills = [_display_skill(s) for s in _infer_skills(f"{title}\n{description or ''}")]
    return DiscoveredJob(
        provider="linkedin",
        external_id=job_id,
        title=title.strip(),
        company_name=(company or "Unknown company").strip(),
        description=description,
        location=location.strip() if location else None,
        remote_type=_remote_type(location, description),
        canonical_url=f"https://www.linkedin.com/jobs/view/{job_id}/",
        source_url=source_url,
        requirements={"skills": skills} if skills else {},
        raw_payload={"source": "linkedin_og_meta", "job_id": job_id},
    )


def _client_headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    }


async def fetch_linkedin_job_from_url(
    url: str,
    *,
    description_override: str | None = None,
) -> DiscoveredJob:
    job_id = extract_linkedin_job_id(url)
    canonical = f"https://www.linkedin.com/jobs/view/{job_id}/"
    parsed = urlparse(url if "://" in url else canonical)
    source_url = url if parsed.scheme else canonical

    guest_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    view_url = canonical

    async with httpx.AsyncClient(
        timeout=30.0, follow_redirects=True, headers=_client_headers()
    ) as client:
        pages: list[tuple[str, str]] = []
        for target in (guest_url, view_url):
            try:
                response = await client.get(target)
            except httpx.HTTPError:
                continue
            if response.status_code == 200 and response.text:
                pages.append((target, response.text))

        for _target, html in pages:
            content_type_guess = "json" if html.lstrip().startswith("{") else "html"
            if content_type_guess == "json":
                try:
                    payload = json.loads(html)
                except json.JSONDecodeError:
                    payload = None
                if isinstance(payload, dict) and payload:
                    job = _legacy_normalize_guest_payload(job_id, payload, source_url)
                    if description_override:
                        job.description = description_override.strip()
                        skills = [
                            _display_skill(s)
                            for s in _infer_skills(f"{job.title}\n{job.description}")
                        ]
                        job.requirements = {"skills": skills} if skills else job.requirements
                    return job

            for parser in (_parse_guest_html, _parse_json_ld, _parse_og_meta):
                job = parser(job_id, html, source_url)
                if job is None:
                    continue
                if description_override and (
                    not job.description or len(job.description) < 200
                ):
                    job.description = description_override.strip()
                    skills = [
                        _display_skill(s)
                        for s in _infer_skills(f"{job.title}\n{job.description or ''}")
                    ]
                    job.requirements = {"skills": skills} if skills else job.requirements
                if job.description or job.title != "LinkedIn job":
                    return job

    if description_override:
        return _manual_fallback(job_id, source_url, description_override)

    raise LinkedInUrlError(
        "fetch_failed",
        "Could not extract job details from LinkedIn. "
        "Paste the job description in the optional field and try again.",
    )


def _legacy_normalize_guest_payload(
    job_id: str, payload: dict[str, Any], source_url: str
) -> DiscoveredJob:
    title = payload.get("title") or payload.get("normalizedTitle") or "LinkedIn job"
    if isinstance(title, dict):
        title = title.get("text") or title.get("name") or "LinkedIn job"
    company = payload.get("companyDetails") or payload.get("company") or {}
    if isinstance(company, dict):
        company_name = (
            company.get("companyName")
            or company.get("name")
            or company.get("universalName")
            or "Unknown company"
        )
    else:
        company_name = str(company or "Unknown company")
    description_html = payload.get("description") or payload.get("jobDescription") or ""
    if isinstance(description_html, dict):
        description_html = description_html.get("text") or description_html.get("html") or ""
    description = _strip_html(str(description_html))
    location = None
    formatted = payload.get("formattedLocation") or payload.get("location")
    if isinstance(formatted, str):
        location = formatted
    elif isinstance(formatted, dict):
        location = formatted.get("default") or formatted.get("name")
    skills = [_display_skill(s) for s in _infer_skills(f"{title}\n{description or ''}")]
    return DiscoveredJob(
        provider="linkedin",
        external_id=job_id,
        title=str(title).strip(),
        company_name=str(company_name).strip() or "Unknown company",
        description=description,
        location=location,
        remote_type=_remote_type(location, description),
        canonical_url=f"https://www.linkedin.com/jobs/view/{job_id}/",
        source_url=source_url,
        requirements={"skills": skills} if skills else {},
        raw_payload={"source": "linkedin_guest_json", "job_id": job_id, "payload": payload},
    )


def _manual_fallback(job_id: str, source_url: str, description: str) -> DiscoveredJob:
    text = description.strip()
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "LinkedIn job")
    skills = [_display_skill(s) for s in _infer_skills(text)]
    return DiscoveredJob(
        provider="linkedin",
        external_id=job_id,
        title=first_line[:120],
        company_name="LinkedIn posting",
        description=text,
        remote_type=_remote_type(None, text),
        canonical_url=f"https://www.linkedin.com/jobs/view/{job_id}/",
        source_url=source_url,
        requirements={"skills": skills} if skills else {},
        raw_payload={"source": "linkedin_manual_description", "job_id": job_id},
    )
