"""Unit tests for heuristic job matching scorer."""

from careerpilot.domains.intelligence.scoring import MODEL_VERSION, score_resume_against_job


def test_high_skill_overlap_scores_high():
    result = score_resume_against_job(
        resume_content={
            "headline": "Senior Data Engineer",
            "skills": ["Python", "SQL", "Spark", "Airflow", "BigQuery"],
            "experience": [
                {
                    "title": "Data Engineer",
                    "company": "Acme",
                    "bullets": ["Built Spark pipelines on BigQuery"],
                }
            ],
        },
        job_title="Senior Data Engineer",
        job_description="Build pipelines with Spark and BigQuery",
        job_requirements={"skills": ["Python", "SQL", "Spark", "BigQuery", "Airflow"]},
        job_remote_type="remote",
    )
    assert result.model_version == MODEL_VERSION
    assert result.score >= 0.8
    assert "python" in result.explanation["matched_skills"]
    assert result.missing_skills == []


def test_missing_skills_are_explained():
    result = score_resume_against_job(
        resume_content={
            "headline": "Backend Engineer",
            "skills": ["Python", "FastAPI"],
            "experience": [],
        },
        job_title="Backend Engineer (Python/FastAPI)",
        job_description="APIs with Postgres and Redis",
        job_requirements={"skills": ["Python", "FastAPI", "PostgreSQL", "Redis"]},
    )
    assert result.score > 0.3
    assert "python" in result.explanation["matched_skills"]
    assert "postgresql" in result.missing_skills
    assert "redis" in result.missing_skills
    assert any("Missing skills" in reason for reason in result.explanation["reasons"])


def test_unrelated_role_scores_low():
    result = score_resume_against_job(
        resume_content={
            "headline": "Graphic Designer",
            "skills": ["Figma", "Illustration"],
            "experience": [{"title": "Designer", "bullets": ["Brand identity work"]}],
        },
        job_title="Senior Data Engineer",
        job_description="Spark BigQuery Airflow pipelines",
        job_requirements={"skills": ["Python", "SQL", "Spark"]},
    )
    assert result.score < 0.25
