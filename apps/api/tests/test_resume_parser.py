from careerpilot.domains.resume.parser.sections import segment_resume_text
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
B.S. Computer Science | State University, CA 2020 | 3.8 CGPA

Skills
Python, SQL, Spark, Airflow
"""

BHARATH = """
Bharath G M
Software Engineer - Data Platform

+91 89714 50169 | skanda70180@gmail.com | Bangalore, IN | linkedin.com/in/bharathx86

PROFESSIONAL OVERVIEW
GCP Certified Data Engineer expert in BigQuery, CDC architecture, ETL/ELT pipeline development, analytics platforms,
dimensional modeling, and enterprise data warehousing.
WORK EXPERIENCE
Associate Software Engineer | Epsilon, Bangalore FEB 2024 – PRESENT
● Designed and owned production-grade GCP ETL/ELT pipelines processing 2–10TB+ retail datasets in BigQuery,
building dimensional models and analytics-ready datasets for forecasting and reporting.
● Architected near real-time PostgreSQL→BigQuery CDC pipelines using GCP Datastream, improving data freshness
and cross-system consistency, with Datadog monitoring
● Reduced BigQuery processing costs by 30% and improved dashboard refresh reliability for business reporting.
● Provisioned GCP infrastructure using Terraform, enabling standardized dev/stage/pre-prod/prod environments
and automated Cloud Run job deployments
● Built an internal LLM-powered analytics assistant using LangChain and MCP, enabling natural-language querying
of forecasting datasets and faster analyst insights
● Developed internal Angular workflow tools and implemented role-based TypeScript-backed access controls for
admin, retailer, supplier, and internal teams
Frontend Developer Intern | Technotharanga Solutions Pvt. Ltd. , Tumkur OCT 2022 – FEB 2023
● Built web interfaces and backend integrations using Node.js and Express for a college management system
PROJECTS
Tracky | Personal Production Analytics Platform FEB 2024 – PRESENT
● Architected and deployed a production full-stack personal analytics platform (Next.js, TypeScript,
Supabase/PostgreSQL) for tracking health, finance, and productivity metrics across structured workflows
● Implemented modular architecture with secure auth, CI/CD pipelines, feature flags, multi-environment
deployments (dev/stage/prod), and LLM-driven personalized onboarding
Real-time Sentiment Analysis|For Epsilon MAY 2024 – AUG 2024
● Developed a real-time social media analytics dashboard using Plotly Dash, multiple social media data via
PySpark and Pandas to identify emerging marketing trends
● Built NLTK + BERT sentiment classification pipelines, enabling campaign teams to monitor public sentiment
and respond rapidly to trending opportunities
EDUCATION
Master of Computer Applications | R V College of Engineering, Bangalore Sep 2024 | 8.75 CGPA
Bachelor of Computer Applications |Seshadripuram College, Tumkur Oct 2022 | 8.57 CGPA
SKILLS
Data Engineering: BigQuery, PostgreSQL, Datastream, PySpark, ETL/ELT, CDC, Data Modeling, Data Warehousing
Cloud & DevOps: Terraform, Docker, CI/CD, Cloud Run
AI: LangChain, RAG, MCP, ACP Languages: Python, SQL, TypeScript, JavaScript
CERTIFICATIONS
GCP Professional Data Engineer | Terraform Associate | Docker & Kubernetes (IBM) | GCP Fundamentals
"""


def test_structure_resume_text_extracts_core_fields():
    content = structure_resume_text(SAMPLE)
    assert content["schema_version"] == "1.1"
    assert "awards" in content
    assert "hobbies" in content
    assert "personal" in content
    assert content["contact"]["name"] == "Jane Doe"
    assert content["contact"]["email"] == "jane.doe@example.com"
    assert content["headline"] == "Senior Data Engineer"
    assert content["experience"]
    assert content["experience"][0]["company"] == "Example Corp"
    assert "Python" in content["skills"]
    assert content["education"][0]["institution"] == "State University"


def test_segment_bharath_resume_sections():
    segments = segment_resume_text(BHARATH)
    order = segments["order"]
    assert "summary" in order
    assert "experience" in order
    assert "projects" in order
    assert "education" in order
    assert "skills" in order
    assert "certifications" in order
    assert "BigQuery" in segments["sections"]["summary"]["text"]
    assert "Epsilon" in segments["sections"]["experience"]["text"]
    assert "Tracky" in segments["sections"]["projects"]["text"]
    assert "State University" not in segments["sections"]["projects"]["text"]
    assert "R V College" in segments["sections"]["education"]["text"]
    assert "BigQuery" in segments["sections"]["skills"]["text"]
    assert "SKILLS" not in segments["sections"]["education"]["text"]


def test_structure_bharath_resume_high_fidelity():
    content = structure_resume_text(BHARATH)

    assert content["contact"]["name"] == "Bharath G M"
    assert content["contact"]["email"] == "skanda70180@gmail.com"
    assert content["contact"]["location"] == "Bangalore, IN"
    assert content["headline"] == "Software Engineer - Data Platform"
    assert content["summary"]
    assert "BigQuery" in content["summary"]

    assert len(content["experience"]) == 2
    first = content["experience"][0]
    assert first["title"] == "Associate Software Engineer"
    assert first["company"] == "Epsilon"
    assert first["location"] == "Bangalore"
    assert first["is_current"] is True
    assert first["start_date"]
    assert len(first["bullets"]) >= 5
    assert not any("SKILLS" in (b or "") for b in first["bullets"])

    second = content["experience"][1]
    assert second["title"] == "Frontend Developer Intern"
    assert "Technotharanga" in (second["company"] or "")

    assert len(content["projects"]) == 2
    tracky = content["projects"][0]
    assert tracky["title"] == "Tracky"
    assert "Analytics Platform" in (tracky["organization"] or "")
    assert tracky["is_current"] is True
    assert "FEB 2024" not in (tracky["title"] or "")
    assert len(tracky["bullets"]) >= 2
    assert all(len(b.split()) > 2 for b in tracky["bullets"])

    assert len(content["education"]) == 2
    mca = content["education"][0]
    assert "Master" in (mca["degree"] or "")
    assert "R V College" in (mca["institution"] or "")
    assert mca["score"] == "8.75"
    assert mca["score_type"] == "cgpa"
    assert "SKILLS" not in (mca["degree"] or "")
    assert "SKILLS" not in (mca["institution"] or "")

    assert "BigQuery" in content["skills"]
    assert "Terraform" in content["skills"]
    assert "Python" in content["skills"]
    assert "Python" not in content["languages"]
    assert not any(s.startswith("Data Engineering") for s in content["skills"])

    cert_titles = [c["title"] for c in content["certifications"]]
    assert "GCP Professional Data Engineer" in cert_titles
    assert "Terraform Associate" in cert_titles
    assert len(cert_titles) >= 4
