from careerpilot.domains.resume.schema import empty_resume_content, normalize_resume_content


def test_empty_resume_content_has_core_and_optional_sections():
    content = empty_resume_content()
    assert content["schema_version"] == "1.1"
    for key in (
        "contact",
        "headline",
        "summary",
        "experience",
        "education",
        "skills",
        "projects",
        "certifications",
        "awards",
        "languages",
        "hobbies",
        "personal",
        "links",
    ):
        assert key in content


def test_normalize_resume_content_upgrades_legacy_payload():
    normalized = normalize_resume_content(
        {
            "schema_version": "1.0",
            "contact": {"name": "Ada", "email": "ada@example.com"},
            "headline": "Engineer",
            "skills": ["Python", {"name": "SQL"}],
            "summary": "Builder.",
        }
    )
    assert normalized["schema_version"] == "1.0"
    assert normalized["contact"]["name"] == "Ada"
    assert normalized["skills"] == ["Python", "SQL"]
    assert normalized["awards"] == []
    assert normalized["hobbies"] == []
    assert normalized["personal"]["job_title"] == "Engineer"


def test_normalize_experience_and_education_fields():
    normalized = normalize_resume_content(
        {
            "experience": [
                {
                    "company": "Acme",
                    "title": "Engineer",
                    "start_date": "2022",
                    "end_date": "Present",
                    "bullets": ["Shipped X"],
                }
            ],
            "education": [
                {
                    "school": "MIT",
                    "degree": "B.S.",
                    "major": "CS",
                    "gpa": "3.9",
                    "is_current": False,
                }
            ],
        }
    )
    exp = normalized["experience"][0]
    assert exp["company"] == "Acme"
    assert exp["is_current"] is True
    assert exp["end_date"] is None
    edu = normalized["education"][0]
    assert edu["institution"] == "MIT"
    assert edu["specialization"] == "CS"
    assert edu["score"] == "3.9"
