"""Import all ORM models so metadata is complete for Alembic."""

from careerpilot.domains.applications.models import (
    Application,
    ApplicationAttempt,
    ApplicationPackage,
    ApplicationStatusHistory,
    Interview,
)
from careerpilot.domains.candidate.models import (
    AutomationPolicy,
    CandidateFact,
    CandidateProfile,
    PreferenceSet,
)
from careerpilot.domains.identity.models import Consent, IntegrationConnection, Session, User
from careerpilot.domains.intelligence.models import (
    FeedbackEvent,
    JobMatch,
    Recommendation,
    SkillGap,
)
from careerpilot.domains.jobs.models import Company, JobPosting, JobSnapshot, JobSource
from careerpilot.domains.platform.models import (
    AgentExecution,
    Approval,
    AuditEvent,
    OutboxEvent,
    Workflow,
    WorkflowTask,
)
from careerpilot.domains.resume.models import (
    Resume,
    ResumeContent,
    ResumeRender,
    ResumeTemplate,
    ResumeVersion,
)

__all__ = [
    "AgentExecution",
    "Application",
    "ApplicationAttempt",
    "ApplicationPackage",
    "ApplicationStatusHistory",
    "Approval",
    "AuditEvent",
    "AutomationPolicy",
    "CandidateFact",
    "CandidateProfile",
    "Company",
    "Consent",
    "FeedbackEvent",
    "IntegrationConnection",
    "Interview",
    "JobMatch",
    "JobPosting",
    "JobSnapshot",
    "JobSource",
    "OutboxEvent",
    "PreferenceSet",
    "Recommendation",
    "Resume",
    "ResumeContent",
    "ResumeRender",
    "ResumeTemplate",
    "ResumeVersion",
    "Session",
    "SkillGap",
    "User",
    "Workflow",
    "WorkflowTask",
]
