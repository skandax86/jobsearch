from careerpilot.domains.resume.parser.ai_extract import (
    attach_source_fact_ids,
    map_ai_resume_payload,
    validate_and_repair_ai_payload,
)
from careerpilot.domains.resume.parser.sections import (
    detect_section_name,
    format_sections_for_prompt,
    segment_resume_text,
)


SAMPLE_RESUME = """
Jane Doe
Data Engineer
jane@example.com | San Francisco, CA
https://linkedin.com/in/janedoe

PROFESSIONAL SUMMARY
Builds reliable data platforms across GCP and Spark.

SKILLS
Python, SQL, BigQuery, Terraform, GCP

EXPERIENCE
Data Engineer
Example Corp
Jan 2022 – Present
• Cut cost 20%
• Shipped Spark jobs

Associate Software Engineer
Epsilon
Jun 2020 – Dec 2021
• Designed production-grade GCP pipelines

PROJECTS
Lakehouse
Personal
• Airflow DAGs for batch + streaming

EDUCATION
B.S. Computer Science
State University
2016 – 2020
CGPA 3.8

CERTIFICATIONS
GCP Data Engineer
Google
2023

AWARDS
Hackathon winner
Example
2021
""".strip()


def test_detect_section_name():
    assert detect_section_name("SKILLS") == "skills"
    assert detect_section_name("Work Experience") == "experience"
    assert detect_section_name("Professional Summary") == "summary"
    assert detect_section_name("Not a heading because it is a long sentence about skills.") is None


def test_segment_resume_text_boundaries():
    segments = segment_resume_text(SAMPLE_RESUME)
    assert "skills" in segments["sections"]
    assert "experience" in segments["sections"]
    assert "projects" in segments["sections"]
    assert "education" in segments["sections"]
    assert "Python" in segments["sections"]["skills"]["text"]
    assert "Example Corp" in segments["sections"]["experience"]["text"]
    assert "Lakehouse" in segments["sections"]["projects"]["text"]
    assert "State University" in segments["sections"]["education"]["text"]
    # No section leakage: education text must not sit inside projects.
    assert "State University" not in segments["sections"]["projects"]["text"]
    prompt = format_sections_for_prompt(segments)
    assert "### SECTION: SKILLS" in prompt
    assert "### SECTION: EXPERIENCE" in prompt


def test_validate_and_repair_rejects_section_leakage():
    repaired = validate_and_repair_ai_payload(
        {
            "summary": "Great engineer.\nSKILLS",
            "skills": ["Python", "this is a very long skill phrase that should die", "SQL"],
            "experience": [
                {
                    "job_title": "• Designed pipelines",
                    "company": "Built dashboards for clients",
                    "achievements": ["real bullet"],
                },
                {
                    "job_title": "Data Engineer",
                    "company": "Example Corp",
                    "end_date": "Present",
                    "currently_working": False,
                    "achievements": ["Cut cost 20%"],
                },
            ],
            "projects": [
                {"title": "EDUCATION", "highlights": []},
                {"title": "Lakehouse", "highlights": ["Airflow"]},
            ],
            "education": [{"degree": "B.S.", "institution": "State University"}],
            "certifications": [],
            "awards": [],
            "linkedin": "https://linkedin.com/in/janedoe",
            "github": "https://linkedin.com/in/janedoe",
        }
    )
    assert repaired["skills"] == ["Python", "SQL"]
    assert len(repaired["experience"]) == 1
    assert repaired["experience"][0]["company"] == "Example Corp"
    assert repaired["experience"][0]["currently_working"] is True
    assert repaired["experience"][0]["end_date"] is None
    assert len(repaired["projects"]) == 1
    assert repaired["projects"][0]["title"] == "Lakehouse"
    assert "SKILLS" not in (repaired["summary"] or "")


def test_map_ai_resume_payload_to_shared_schema():
    mapped = map_ai_resume_payload(
        {
            "full_name": "Jane Doe",
            "headline": "Data Engineer",
            "email": "jane@example.com",
            "phone": "+1 555 0100",
            "location": "San Francisco, CA",
            "linkedin": "https://linkedin.com/in/janedoe",
            "github": "https://github.com/janedoe",
            "summary": "Builds reliable data platforms.",
            "skills": ["Python", "SQL", "Spark"],
            "experience": [
                {
                    "job_title": "Data Engineer",
                    "company": "Example Corp",
                    "location": "Remote",
                    "start_date": "Jan 2022",
                    "end_date": "Present",
                    "currently_working": True,
                    "summary": "Owned pipelines.",
                    "achievements": ["Cut cost 20%", "Shipped Spark jobs"],
                }
            ],
            "education": [
                {
                    "degree": "B.S. Computer Science",
                    "institution": "State University",
                    "location": "CA",
                    "start_date": "2016",
                    "end_date": "2020",
                    "cgpa": "3.8",
                    "specialization": "CS",
                }
            ],
            "projects": [
                {
                    "title": "Lakehouse",
                    "organization": "Personal",
                    "summary": "Batch + streaming",
                    "highlights": ["Airflow DAGs"],
                    "technologies": ["Python", "dbt"],
                }
            ],
            "certifications": [
                {
                    "name": "GCP DE",
                    "issuer": "Google",
                    "issue_date": "2023",
                    "credential_url": "https://example.com/cert",
                }
            ],
            "awards": [{"title": "Hackathon winner", "issuer": "Example", "date": "2021"}],
        }
    )

    assert mapped["contact"]["name"] == "Jane Doe"
    assert mapped["contact"]["email"] == "jane@example.com"
    assert "https://linkedin.com/in/janedoe" in mapped["contact"]["links"]
    assert mapped["headline"] == "Data Engineer"
    assert "Python" in mapped["skills"]
    exp = mapped["experience"][0]
    assert exp["title"] == "Data Engineer"
    assert exp["company"] == "Example Corp"
    assert exp["is_current"] is True
    assert exp["end_date"] is None
    assert "Cut cost 20%" in exp["bullets"]
    edu = mapped["education"][0]
    assert edu["institution"] == "State University"
    assert edu["score"] == "3.8"
    assert edu["score_type"] == "cgpa"
    assert mapped["projects"][0]["title"] == "Lakehouse"
    assert mapped["certifications"][0]["title"] == "GCP DE"
    assert mapped["awards"][0]["title"] == "Hackathon winner"


def test_map_ai_resume_payload_handles_empty():
    mapped = map_ai_resume_payload({})
    assert mapped["contact"]["name"] is None
    assert mapped["skills"] == []
    assert mapped["experience"] == []


def test_validate_unwraps_confidence_and_filters_programming_languages():
    from careerpilot.domains.resume.parser.ai_extract import validate_and_repair_ai_payload

    repaired = validate_and_repair_ai_payload(
        {
            "full_name": {"value": "Jane Doe", "confidence": 0.99},
            "skills": ["Python", "SQL"],
            "skill_groups": {"ai": ["LangChain"]},
            "languages": ["English", "Python"],
            "experience": [
                {
                    "job_title": {"value": "Engineer", "confidence": 0.9},
                    "company": {"value": "Epsilon", "confidence": 0.95},
                    "achievements": ["Built pipelines"],
                }
            ],
            "projects": [
                {
                    "title": "Tracky | Platform FEB 2024 – PRESENT",
                    "highlights": ["Shipped"],
                }
            ],
            "education": [],
            "certifications": [],
            "awards": [],
        }
    )
    assert repaired["full_name"] == "Jane Doe"
    assert "LangChain" in repaired["skills"]
    assert "Python" in repaired["skills"]
    assert repaired["languages"] == ["English"]
    assert repaired["experience"][0]["job_title"] == "Engineer"
    assert repaired["experience"][0]["company"] == "Epsilon"
    assert "FEB 2024" not in repaired["projects"][0]["title"]
    assert repaired["projects"][0]["currently_working"] is True


def test_attach_source_fact_ids():
    mapped = map_ai_resume_payload(
        {
            "full_name": "Jane Doe",
            "experience": [
                {
                    "job_title": "Data Engineer",
                    "company": "Example Corp",
                    "achievements": ["Cut cost 20%"],
                }
            ],
            "education": [{"degree": "B.S. Computer Science", "institution": "State University"}],
            "projects": [{"title": "Lakehouse", "highlights": ["Airflow DAGs"]}],
            "skills": [],
            "certifications": [],
            "awards": [],
        }
    )
    grounded = attach_source_fact_ids(mapped, SAMPLE_RESUME)
    assert grounded["experience"][0]["source_fact_ids"]
    assert any(fid.startswith("L") for fid in grounded["experience"][0]["source_fact_ids"])
    assert grounded["education"][0]["source_fact_ids"]
    assert grounded["projects"][0]["source_fact_ids"]
