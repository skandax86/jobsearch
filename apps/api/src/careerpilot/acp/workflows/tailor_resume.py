"""ACP TailorResumeWorkflow — propose edits for a target job."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careerpilot.acp.orchestrator import AcpWorkflowResult, acp
from careerpilot.domains.candidate.models import CandidateProfile
from careerpilot.domains.jobs.models import JobPosting
from careerpilot.domains.platform.models import Workflow
from careerpilot.domains.resume.models import Resume, ResumeVersion
from careerpilot.domains.resume.schema import normalize_resume_content
from careerpilot.domains.resume.tailor import suggest_resume_tailoring

WORKFLOW_TYPE = "tailor_resume"


async def run_tailor_resume_workflow(
    db: AsyncSession,
    *,
    workflow: Workflow,
    input_payload: dict[str, Any],
) -> AcpWorkflowResult:
    resume_id = input_payload.get("resume_id")
    if not resume_id:
        return AcpWorkflowResult(status="failed", error="resume_id is required.")

    task_log: list[dict[str, Any]] = []

    resume = await db.scalar(
        select(Resume)
        .where(Resume.id == uuid.UUID(str(resume_id)))
        .options(selectinload(Resume.versions).selectinload(ResumeVersion.content))
    )
    if resume is None:
        return AcpWorkflowResult(status="failed", error="Resume not found.")

    version = None
    if resume.active_version_id:
        for item in resume.versions:
            if item.id == resume.active_version_id:
                version = item
                break
    if version is None and resume.versions:
        version = resume.versions[0]
    if version is None or version.content is None:
        return AcpWorkflowResult(status="failed", error="Resume has no parsed content.")

    content = normalize_resume_content(version.content.content)
    await acp.record_task(
        db,
        workflow=workflow,
        task_type="load_resume",
        agent_name="resume",
        payload={"resume_id": str(resume.id)},
        result={"status": resume.status},
        status="completed",
    )
    task_log.append({"step": "load_resume", "status": "SUCCESS"})

    job_title = str(input_payload.get("job_title") or "Target Role")
    job_description = input_payload.get("job_description")
    job_requirements = input_payload.get("job_requirements")
    company_name = input_payload.get("company_name")
    job_posting_id = input_payload.get("job_posting_id")

    if job_posting_id:
        job = await db.scalar(
            select(JobPosting)
            .where(JobPosting.id == uuid.UUID(str(job_posting_id)))
            .options(selectinload(JobPosting.snapshots))
        )
        if job is not None:
            job_title = job.title or job_title
            company_name = job.company_name or company_name
            snap = job.snapshots[0] if job.snapshots else None
            if snap is not None:
                job_description = snap.description_text or job_description
                job_requirements = snap.requirements or job_requirements

    await acp.record_task(
        db,
        workflow=workflow,
        task_type="load_job",
        agent_name="search",
        payload={"job_posting_id": job_posting_id, "job_title": job_title},
        result={"company": company_name},
        status="completed",
    )
    task_log.append({"step": "load_job", "status": "SUCCESS"})

    proposal = suggest_resume_tailoring(
        resume_content=content,
        job_title=job_title,
        job_description=job_description if isinstance(job_description, str) else None,
        job_requirements=job_requirements if isinstance(job_requirements, dict) else None,
        company_name=company_name if isinstance(company_name, str) else None,
    )
    await acp.record_task(
        db,
        workflow=workflow,
        task_type="propose",
        agent_name="optimizer",
        payload={},
        result={"suggestion_count": len(proposal.get("suggestions") or [])},
        status="completed",
    )
    task_log.append({"step": "propose", "status": "SUCCESS"})

    # Human selection happens in UI; workflow returns proposals (needs_review).
    await acp.record_task(
        db,
        workflow=workflow,
        task_type="human_select",
        agent_name="supervisor",
        payload={"gate": "await_ui_selection"},
        result={"waiting": True},
        status="completed",
    )
    task_log.append({"step": "human_select", "status": "SUCCESS"})

    return AcpWorkflowResult(
        status="needs_review",
        output={
            "resume_id": str(resume.id),
            "job_title": job_title,
            "company_name": company_name,
            "job_posting_id": job_posting_id,
            "proposal": proposal,
            "orchestration": "acp",
        },
        tasks=task_log,
    )


async def start_tailor_resume(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> tuple[Workflow, AcpWorkflowResult]:
    # Ownership soft-check via profile linkage
    profile = await db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user_id))
    if profile is None:
        raise ValueError("Candidate profile required.")
    return await acp.start(
        db,
        user_id=user_id,
        workflow_type=WORKFLOW_TYPE,
        input_payload={"resume_id": str(resume_id), **payload},
        correlation_id=correlation_id or str(resume_id),
    )


acp.register(WORKFLOW_TYPE, run_tailor_resume_workflow)
