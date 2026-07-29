"""Unit tests for resume tailor suggestions."""

from __future__ import annotations

from careerpilot.domains.resume.tailor import apply_suggestions, suggest_resume_tailoring


def test_suggest_adds_missing_skills_and_headline():
    resume = {
        "schema_version": "1.0",
        "headline": "Backend Engineer",
        "summary": "Built APIs at scale.",
        "skills": ["Python", "SQL"],
        "experience": [
            {
                "id": "experience_01",
                "company": "Acme",
                "title": "Engineer",
                "bullets": ["Shipped billing APIs."],
            }
        ],
    }
    result = suggest_resume_tailoring(
        resume_content=resume,
        job_title="Senior Platform Engineer",
        job_description="Looking for Kubernetes and AWS experience with Python.",
        job_requirements={"skills": ["Python", "Kubernetes", "AWS"]},
        company_name="Globex",
    )
    ids = {s["id"] for s in result["suggestions"]}
    assert "skills" in ids
    assert "headline" in ids
    assert "kubernetes" in [s.lower() for s in result["proposed_content"]["skills"]]
    assert "AWS" in result["proposed_content"]["skills"] or "Aws" in result["proposed_content"]["skills"]
    assert result["match_preview"]["missing_skills"]


def test_apply_suggestions_respects_selection():
    resume = {
        "headline": "Engineer",
        "summary": "Hello",
        "skills": ["Python"],
        "experience": [],
    }
    result = suggest_resume_tailoring(
        resume_content=resume,
        job_title="Data Engineer",
        job_description="Need Spark",
        job_requirements={"skills": ["Python", "Spark"]},
        company_name="Initech",
    )
    skills_only = apply_suggestions(
        result["current_content"],
        result["suggestions"],
        selected_ids=["skills"],
    )
    assert skills_only["headline"] == "Engineer"
    assert any("spark" in s.lower() for s in skills_only["skills"])


def test_generate_cover_letter_mentions_role_and_company():
    from careerpilot.domains.resume.tailor import generate_cover_letter

    letter = generate_cover_letter(
        resume_content={
            "contact": {"name": "Bharath G M", "email": "bharath@example.com"},
            "headline": "Data Engineer",
            "summary": "Built reliable data pipelines.",
            "skills": ["Python", "Spark", "SQL"],
            "experience": [
                {
                    "title": "Data Engineer",
                    "company": "Acme",
                    "bullets": ["Built Spark pipelines that cut processing time by 40%."],
                }
            ],
        },
        job_title="Cloud Data Engineer",
        job_description="Need Python, Spark, and GCP.",
        job_requirements={"skills": ["Python", "Spark", "GCP"]},
        company_name="Google",
    )
    assert "Cloud Data Engineer" in letter["text"]
    assert "Google" in letter["text"]
    assert "Bharath G M" in letter["text"]
    assert letter["subject"].startswith("Application for Cloud Data Engineer")
