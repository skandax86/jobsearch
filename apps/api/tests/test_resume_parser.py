from careerpilot.domains.resume.parser.structure import structure_resume_text

SAMPLE = """
Jane Doe
Senior Data Engineer
jane.doe@example.com | +1 555-010-2000 | San Francisco, CA
https://linkedin.com/in/janedoe

Summary
Data engineer with experience building reliable pipelines.

Experience
Data Engineer at Example Corp | Jan 2022 - Present
• Built Spark pipelines for analytics
• Reduced warehouse cost by 20%

Education
State University
B.S. Computer Science

Skills
Python, SQL, Spark, Airflow
"""


def test_structure_resume_text_extracts_core_fields():
    content = structure_resume_text(SAMPLE)
    assert content["schema_version"] == "1.0"
    assert content["contact"]["name"] == "Jane Doe"
    assert content["contact"]["email"] == "jane.doe@example.com"
    assert content["headline"] == "Senior Data Engineer"
    assert content["experience"]
    assert content["experience"][0]["company"] == "Example Corp"
    assert "Python" in content["skills"]
    assert content["education"][0]["institution"] == "State University"
