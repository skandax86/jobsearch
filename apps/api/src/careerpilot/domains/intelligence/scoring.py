"""Deterministic resume–job scoring (heuristic-v1).

Produces explainable scores without an external embedding provider.
Semantic/pgvector matching can plug in later under a new model_version.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

MODEL_VERSION = "heuristic-v1"

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+.#-]{1,}")
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "or",
        "the",
        "to",
        "of",
        "in",
        "on",
        "for",
        "with",
        "at",
        "by",
        "from",
        "as",
        "is",
        "are",
        "be",
        "this",
        "that",
        "our",
        "your",
        "we",
        "you",
        "will",
        "job",
        "role",
        "team",
        "work",
        "experience",
        "years",
        "strong",
        "preferred",
        "required",
        "using",
        "etc",
    }
)


def normalize_skill(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def tokenize(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1}


def extract_resume_skills(content: dict[str, Any]) -> list[str]:
    skills: list[str] = []
    raw = content.get("skills") or []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str) and item.strip():
                skills.append(item.strip())
            elif isinstance(item, dict):
                name = item.get("name") or item.get("skill")
                if isinstance(name, str) and name.strip():
                    skills.append(name.strip())
    return skills


def extract_job_skills(job: dict[str, Any]) -> list[str]:
    requirements = job.get("requirements") or {}
    skills: list[str] = []
    if isinstance(requirements, dict):
        raw = requirements.get("skills") or []
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str) and item.strip():
                    skills.append(item.strip())
    return skills


def _resume_text_blob(content: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("headline", "summary"):
        value = content.get(key)
        if isinstance(value, str):
            parts.append(value)
    for skill in extract_resume_skills(content):
        parts.append(skill)
    for exp in content.get("experience") or []:
        if not isinstance(exp, dict):
            continue
        for key in ("title", "company", "summary"):
            value = exp.get(key)
            if isinstance(value, str):
                parts.append(value)
        for bullet in exp.get("bullets") or []:
            if isinstance(bullet, str):
                parts.append(bullet)
    for project in content.get("projects") or []:
        if not isinstance(project, dict):
            continue
        for key in ("name", "description"):
            value = project.get(key)
            if isinstance(value, str):
                parts.append(value)
    return "\n".join(parts)


@dataclass(frozen=True)
class MatchScore:
    score: float
    confidence: float
    features: dict[str, Any]
    explanation: dict[str, Any]
    missing_skills: list[str]
    model_version: str = MODEL_VERSION


def score_resume_against_job(
    *,
    resume_content: dict[str, Any],
    job_title: str,
    job_description: str | None,
    job_requirements: dict[str, Any] | None,
    job_remote_type: str | None = None,
    preferred_remote: str | None = None,
) -> MatchScore:
    job_payload = {
        "title": job_title,
        "description": job_description,
        "requirements": job_requirements or {},
        "remote_type": job_remote_type,
    }

    resume_skills = [normalize_skill(s) for s in extract_resume_skills(resume_content)]
    resume_skill_set = {s for s in resume_skills if s}
    job_skills = [normalize_skill(s) for s in extract_job_skills(job_payload) if normalize_skill(s)]
    job_skill_set = set(job_skills)

    matched = sorted(resume_skill_set & job_skill_set)
    missing = sorted(job_skill_set - resume_skill_set)

    skill_coverage = len(matched) / len(job_skill_set) if job_skill_set else 0.0

    resume_tokens = tokenize(_resume_text_blob(resume_content))
    title_tokens = tokenize(job_title)
    title_similarity = (
        len(resume_tokens & title_tokens) / len(title_tokens) if title_tokens else 0.0
    )

    desc_tokens = tokenize(job_description or "")
    keyword_pool = title_tokens | {t for t in desc_tokens if len(t) > 3}
    if keyword_pool:
        keyword_presence = len(resume_tokens & keyword_pool) / min(len(keyword_pool), 40)
        keyword_presence = min(keyword_presence, 1.0)
    else:
        keyword_presence = 0.0

    remote_bonus = 0.0
    if preferred_remote and job_remote_type:
        if preferred_remote.lower() == job_remote_type.lower():
            remote_bonus = 0.05
        elif preferred_remote.lower() == "remote" and job_remote_type.lower() != "onsite":
            remote_bonus = 0.02

    # When job lists skills, weight coverage heavily; otherwise lean on text signals.
    if job_skill_set:
        score = (
            0.55 * skill_coverage + 0.25 * title_similarity + 0.20 * keyword_presence + remote_bonus
        )
    else:
        score = 0.45 * title_similarity + 0.55 * keyword_presence + remote_bonus

    score = round(max(0.0, min(1.0, score)), 4)

    signal_bits = 0
    if resume_skill_set:
        signal_bits += 1
    if job_skill_set:
        signal_bits += 1
    if title_tokens:
        signal_bits += 1
    if resume_tokens:
        signal_bits += 1
    confidence = round(min(1.0, 0.35 + 0.15 * signal_bits + 0.2 * skill_coverage), 4)

    reasons: list[str] = []
    if matched:
        reasons.append(f"Matched skills: {', '.join(matched[:8])}.")
    if missing:
        reasons.append(f"Missing skills: {', '.join(missing[:8])}.")
    if title_similarity >= 0.4:
        reasons.append("Job title aligns with resume keywords.")
    elif title_similarity > 0:
        reasons.append("Partial title keyword overlap.")
    if not reasons:
        reasons.append("Limited structured signal; score based on keyword overlap.")

    features = {
        "skill_coverage": round(skill_coverage, 4),
        "title_similarity": round(title_similarity, 4),
        "keyword_presence": round(keyword_presence, 4),
        "remote_bonus": remote_bonus,
        "resume_skill_count": len(resume_skill_set),
        "job_skill_count": len(job_skill_set),
        "matched_skill_count": len(matched),
    }
    explanation = {
        "model": MODEL_VERSION,
        "matched_skills": matched,
        "missing_skills": missing,
        "reasons": reasons,
    }
    return MatchScore(
        score=score,
        confidence=confidence,
        features=features,
        explanation=explanation,
        missing_skills=missing,
    )
