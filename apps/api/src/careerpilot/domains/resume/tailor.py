"""Heuristic resume-tailoring suggestions for a target job (UI-only apply)."""

from __future__ import annotations

import copy
import re
from typing import Any

from careerpilot.domains.intelligence.scoring import (
    extract_job_skills,
    extract_resume_skills,
    normalize_skill,
    score_resume_against_job,
    tokenize,
)

_TITLE_STOP = frozenset(
    {
        "senior",
        "junior",
        "lead",
        "staff",
        "principal",
        "i",
        "ii",
        "iii",
        "sr",
        "jr",
        "the",
        "and",
        "of",
        "for",
        "a",
        "an",
    }
)


def _job_skill_list(job_title: str, description: str | None, requirements: dict[str, Any] | None) -> list[str]:
    skills = extract_job_skills({"requirements": requirements or {}})
    if skills:
        return skills
    # Fallback: pull capitalized / known tokens from title+description via scoring helpers
    blob = f"{job_title}\n{description or ''}"
    tokens = sorted(tokenize(blob))
    # Prefer multi-char tokens that look like skills (already filtered stopwords)
    return [t for t in tokens if len(t) >= 3][:12]


def _display_skills(skills: list[str]) -> list[str]:
    return [s.title() if s.islower() else s for s in skills]


def suggest_resume_tailoring(
    *,
    resume_content: dict[str, Any],
    job_title: str,
    job_description: str | None,
    job_requirements: dict[str, Any] | None,
    company_name: str | None = None,
) -> dict[str, Any]:
    current = copy.deepcopy(resume_content if isinstance(resume_content, dict) else {})
    job_skills = [
        normalize_skill(s)
        for s in _job_skill_list(job_title, job_description, job_requirements)
        if normalize_skill(s)
    ]
    # Prefer structured requirements skills when present
    req_skills = [
        normalize_skill(s)
        for s in extract_job_skills({"requirements": job_requirements or {}})
        if normalize_skill(s)
    ]
    if req_skills:
        job_skills = req_skills

    resume_skills = [normalize_skill(s) for s in extract_resume_skills(current)]
    resume_set = {s for s in resume_skills if s}
    job_set = {s for s in job_skills if s}
    missing = sorted(job_set - resume_set)
    matched = sorted(resume_set & job_set)

    score = score_resume_against_job(
        resume_content=current,
        job_title=job_title,
        job_description=job_description,
        job_requirements=job_requirements,
    )

    suggestions: list[dict[str, Any]] = []

    # 1) Headline
    current_headline = current.get("headline") if isinstance(current.get("headline"), str) else ""
    title_bits = [
        w
        for w in re.findall(r"[A-Za-z][A-Za-z+#.]{1,}", job_title)
        if w.lower() not in _TITLE_STOP
    ]
    focus = " ".join(title_bits[:4]) or job_title
    company_bit = f" | {company_name}" if company_name else ""
    proposed_headline = f"{focus}{company_bit}".strip(" |")
    if current_headline.strip().lower() != proposed_headline.lower():
        suggestions.append(
            {
                "id": "headline",
                "section": "headline",
                "title": "Align headline with the target role",
                "rationale": f"Mirror the job title language so recruiters scanning for “{focus}” see an immediate match.",
                "path": "headline",
                "before": current_headline or None,
                "after": proposed_headline,
                "selected_by_default": True,
            }
        )

    # 2) Summary
    current_summary = current.get("summary") if isinstance(current.get("summary"), str) else ""
    skill_phrase = ", ".join(_display_skills(missing[:5])) if missing else ", ".join(
        _display_skills(matched[:5])
    )
    company_ref = company_name or "this company"
    proposed_summary = (
        f"Targeting {job_title} at {company_ref}. "
        f"{current_summary.strip() if current_summary.strip() else 'Experienced professional delivering measurable outcomes.'} "
        f"Emphasizing {skill_phrase or 'relevant domain skills'} aligned to this posting."
    ).strip()
    if proposed_summary != current_summary.strip():
        suggestions.append(
            {
                "id": "summary",
                "section": "summary",
                "title": "Sharpen summary for this posting",
                "rationale": "Lead with the target role and weave in skills the job emphasizes.",
                "path": "summary",
                "before": current_summary or None,
                "after": proposed_summary,
                "selected_by_default": True,
            }
        )

    # 3) Skills
    if missing:
        after_skills = list(extract_resume_skills(current))
        for skill in _display_skills(missing):
            if normalize_skill(skill) not in {normalize_skill(s) for s in after_skills}:
                after_skills.append(skill)
        suggestions.append(
            {
                "id": "skills",
                "section": "skills",
                "title": "Add missing skills from the job",
                "rationale": f"These appear in the job requirements but not on your resume: {', '.join(missing[:10])}.",
                "path": "skills",
                "before": extract_resume_skills(current),
                "after": after_skills,
                "selected_by_default": True,
            }
        )

    # 4) Latest experience bullets
    experience = current.get("experience") if isinstance(current.get("experience"), list) else []
    if experience and isinstance(experience[0], dict) and missing:
        exp0 = experience[0]
        bullets = [b for b in (exp0.get("bullets") or []) if isinstance(b, str)]
        keywords = _display_skills(missing[:3])
        new_bullet = (
            f"Applied {', '.join(keywords)} to deliver outcomes relevant to {job_title}."
        )
        # Avoid duplicating near-identical bullet
        if not any(normalize_skill(new_bullet[:40]) in normalize_skill(b) for b in bullets):
            after_bullets = [*bullets, new_bullet]
            suggestions.append(
                {
                    "id": "experience_0_bullets",
                    "section": "experience",
                    "title": "Add a role-aligned bullet to latest experience",
                    "rationale": "Surface keywords from the posting in your most recent role so ATS and humans both see the fit.",
                    "path": "experience.0.bullets",
                    "before": bullets,
                    "after": after_bullets,
                    "selected_by_default": True,
                }
            )

    if not suggestions:
        suggestions.append(
            {
                "id": "no_op",
                "section": "general",
                "title": "Resume already aligns well",
                "rationale": "No high-confidence structural tweaks were found for this posting.",
                "path": "",
                "before": None,
                "after": None,
                "selected_by_default": False,
            }
        )

    proposed = apply_suggestions(
        current,
        suggestions,
        selected_ids=[s["id"] for s in suggestions if s.get("selected_by_default")],
    )

    return {
        "model_version": "tailor-heuristic-v1",
        "match_preview": {
            "score": score.score,
            "confidence": score.confidence,
            "matched_skills": matched,
            "missing_skills": missing,
            "reasons": score.explanation.get("reasons", []),
        },
        "suggestions": [s for s in suggestions if s["id"] != "no_op"] or suggestions,
        "current_content": current,
        "proposed_content": proposed,
    }


def apply_suggestions(
    content: dict[str, Any],
    suggestions: list[dict[str, Any]],
    *,
    selected_ids: list[str],
) -> dict[str, Any]:
    result = copy.deepcopy(content)
    selected = set(selected_ids)
    by_id = {s["id"]: s for s in suggestions}
    for sid in selected_ids:
        suggestion = by_id.get(sid)
        if not suggestion or sid not in selected:
            continue
        path = suggestion.get("path") or ""
        if not path:
            continue
        _set_path(result, path, copy.deepcopy(suggestion.get("after")))
    return result


def generate_cover_letter(
    *,
    resume_content: dict[str, Any],
    job_title: str,
    job_description: str | None,
    job_requirements: dict[str, Any] | None,
    company_name: str | None = None,
) -> dict[str, Any]:
    content = resume_content if isinstance(resume_content, dict) else {}
    contact = content.get("contact") if isinstance(content.get("contact"), dict) else {}
    name = contact.get("name") if isinstance(contact.get("name"), str) else None
    email = contact.get("email") if isinstance(contact.get("email"), str) else None
    location = contact.get("location") if isinstance(contact.get("location"), str) else None
    headline = content.get("headline") if isinstance(content.get("headline"), str) else None
    summary = content.get("summary") if isinstance(content.get("summary"), str) else None

    resume_skills = extract_resume_skills(content)
    req_skills = [
        normalize_skill(s)
        for s in extract_job_skills({"requirements": job_requirements or {}})
        if normalize_skill(s)
    ]
    job_skills = req_skills or [
        normalize_skill(s)
        for s in _job_skill_list(job_title, job_description, job_requirements)
        if normalize_skill(s)
    ]
    resume_set = {normalize_skill(s) for s in resume_skills}
    matched = sorted(resume_set & set(job_skills))
    highlight_skills = _display_skills(matched[:6] or [normalize_skill(s) for s in resume_skills[:5]])

    experience = content.get("experience") if isinstance(content.get("experience"), list) else []
    latest = experience[0] if experience and isinstance(experience[0], dict) else {}
    latest_title = latest.get("title") if isinstance(latest.get("title"), str) else None
    latest_company = latest.get("company") if isinstance(latest.get("company"), str) else None
    latest_bullet = None
    for bullet in latest.get("bullets") or []:
        if isinstance(bullet, str) and bullet.strip():
            latest_bullet = bullet.strip()
            break

    company = (company_name or "your team").strip()
    candidate = (name or "Candidate").strip()
    role = job_title.strip() or "this role"

    opener_bits = []
    if headline:
        opener_bits.append(headline.strip().rstrip("."))
    if latest_title and latest_company:
        opener_bits.append(f"most recently as {latest_title} at {latest_company}")
    elif latest_title:
        opener_bits.append(f"most recently as {latest_title}")
    opener = (
        f"I am writing to apply for the {role} position at {company}."
        if not opener_bits
        else (
            f"I am writing to apply for the {role} position at {company}. "
            f"I am a {opener_bits[0]}"
            + (f", {opener_bits[1]}" if len(opener_bits) > 1 else "")
            + "."
        )
    )

    skill_sentence = (
        f"My background includes hands-on work with {', '.join(highlight_skills)}, "
        f"which aligns closely with the requirements for this role."
        if highlight_skills
        else "My experience aligns closely with the requirements described in this posting."
    )

    impact_sentence = (
        f"In my recent work, {latest_bullet[0].lower() + latest_bullet[1:]}."
        if latest_bullet and latest_bullet[0].isupper()
        else f"In my recent work, {latest_bullet}."
        if latest_bullet
        else (
            summary.strip()
            if isinstance(summary, str) and summary.strip()
            else "I have delivered measurable outcomes across data platforms, reliability, and stakeholder collaboration."
        )
    )
    if impact_sentence and not impact_sentence.endswith("."):
        impact_sentence += "."

    why_company = (
        f"I am especially interested in {company} because this {role} role is a strong fit "
        f"for my experience building and operating data systems at scale."
    )
    close = (
        "I would welcome the opportunity to discuss how I can contribute to your team. "
        "Thank you for your time and consideration."
    )

    body_paragraphs = [opener, skill_sentence, impact_sentence, why_company, close]
    letter = "\n\n".join(body_paragraphs)

    header_lines = [candidate]
    if email:
        header_lines.append(email)
    if location:
        header_lines.append(location)
    header = "\n".join(header_lines)

    full_text = f"{header}\n\nDear Hiring Manager,\n\n{letter}\n\nSincerely,\n{candidate}\n"

    return {
        "model_version": "cover-letter-heuristic-v1",
        "tone": "professional",
        "recipient": "Hiring Manager",
        "subject": f"Application for {role} — {candidate}",
        "text": full_text.strip() + "\n",
        "highlights": {
            "matched_skills": highlight_skills,
            "latest_role": latest_title,
            "latest_company": latest_company,
        },
    }


def _set_path(root: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cur: Any = root
    for i, part in enumerate(parts[:-1]):
        nxt = parts[i + 1] if i + 1 < len(parts) else None
        if part.isdigit():
            idx = int(part)
            if not isinstance(cur, list):
                return
            while len(cur) <= idx:
                cur.append({})
            cur = cur[idx]
        else:
            if part not in cur or not isinstance(cur[part], (dict, list)):
                # Create container based on next segment
                cur[part] = [] if (nxt and nxt.isdigit()) else {}
            cur = cur[part]
    last = parts[-1]
    if last.isdigit():
        idx = int(last)
        if not isinstance(cur, list):
            return
        while len(cur) <= idx:
            cur.append(None)
        cur[idx] = value
    elif isinstance(cur, dict):
        cur[last] = value
