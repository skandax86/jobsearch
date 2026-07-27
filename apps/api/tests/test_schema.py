"""Smoke tests for SQLAlchemy schema registry."""

from careerpilot.db import models as _models  # noqa: F401
from careerpilot.db.base import Base

EXPECTED_TABLES = {
    "users",
    "sessions",
    "consents",
    "integration_connections",
    "candidate_profiles",
    "candidate_facts",
    "preferences",
    "automation_policies",
    "resumes",
    "resume_versions",
    "resume_contents",
    "resume_templates",
    "resume_renders",
    "companies",
    "job_postings",
    "job_sources",
    "job_snapshots",
    "job_matches",
    "skill_gaps",
    "recommendations",
    "feedback_events",
    "applications",
    "application_packages",
    "application_attempts",
    "status_history",
    "interviews",
    "workflows",
    "workflow_tasks",
    "agent_executions",
    "approvals",
    "outbox_events",
    "audit_events",
}


def test_all_documented_tables_are_registered():
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_embedding_columns_use_pgvector():
    resume_versions = Base.metadata.tables["resume_versions"]
    job_postings = Base.metadata.tables["job_postings"]
    assert str(resume_versions.c.embedding.type) == "VECTOR(1536)"
    assert str(job_postings.c.embedding.type) == "VECTOR(1536)"
