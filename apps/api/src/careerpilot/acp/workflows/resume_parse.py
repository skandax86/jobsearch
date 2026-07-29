"""ACP ResumeParseWorkflow — coordinates resume MCP tools."""

from __future__ import annotations

import base64
import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.acp.orchestrator import AcpWorkflowResult, acp
from careerpilot.config import settings
from careerpilot.domains.platform.models import Workflow
from careerpilot.domains.resume.schema import normalize_resume_content
from careerpilot.mcp.resume.server import call_resume_tool

logger = logging.getLogger(__name__)

WORKFLOW_TYPE = "resume_parse"


def _merge_resume_content(primary: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    merged = dict(primary)
    for key in (
        "experience",
        "education",
        "projects",
        "certifications",
        "awards",
        "skills",
        "languages",
        "hobbies",
    ):
        if not merged.get(key) and fallback.get(key):
            merged[key] = fallback[key]
    if not merged.get("summary") and fallback.get("summary"):
        merged["summary"] = fallback["summary"]
    if not merged.get("headline") and fallback.get("headline"):
        merged["headline"] = fallback["headline"]
    contact = dict(merged.get("contact") or {})
    fb_contact = fallback.get("contact") or {}
    for field in ("name", "email", "phone", "location"):
        if not contact.get(field) and fb_contact.get(field):
            contact[field] = fb_contact[field]
    if not contact.get("links") and fb_contact.get("links"):
        contact["links"] = fb_contact["links"]
    merged["contact"] = contact
    return normalize_resume_content(merged)


async def run_resume_parse_workflow(
    db: AsyncSession,
    *,
    workflow: Workflow,
    input_payload: dict[str, Any],
) -> AcpWorkflowResult:
    """
    Steps (via MCP):
      1. extract_resume_text
      2. segment_resume_sections
      3. structure_resume_heuristic
      4. structure_resume_ai (optional)
      5. validate_resume_json
    """
    mime_type = str(input_payload.get("mime_type") or "")
    data_b64 = input_payload.get("data_b64")
    if not mime_type or not data_b64:
        return AcpWorkflowResult(
            status="failed",
            error="mime_type and data_b64 are required.",
        )

    task_log: list[dict[str, Any]] = []

    # 1) Extract text
    extract = await call_resume_tool(
        "extract_resume_text",
        mime_type=mime_type,
        data_b64=data_b64,
    )
    await acp.record_task(
        db,
        workflow=workflow,
        task_type="extract_text",
        agent_name="resume_extract_agent",
        payload={"mime_type": mime_type},
        result={"char_count": (extract.result or {}).get("char_count")},
        status="completed" if extract.status == "SUCCESS" else "failed",
        error=(extract.error or {}).get("message") if extract.error else None,
    )
    task_log.append({"step": "extract_text", "status": extract.status})
    if extract.status != "SUCCESS":
        return AcpWorkflowResult(
            status="failed",
            error=(extract.error or {}).get("message") or "Text extraction failed.",
            tasks=task_log,
        )
    raw_text = str((extract.result or {}).get("text") or "")

    # 2) Segment
    segment = await call_resume_tool("segment_resume_sections", text=raw_text)
    await acp.record_task(
        db,
        workflow=workflow,
        task_type="segment_sections",
        agent_name="resume_section_agent",
        payload={"char_count": len(raw_text)},
        result={"order": (segment.result or {}).get("order")},
        status="completed" if segment.status == "SUCCESS" else "failed",
        error=(segment.error or {}).get("message") if segment.error else None,
    )
    task_log.append({"step": "segment_sections", "status": segment.status})

    # 3) Heuristic structure
    heuristic_res = await call_resume_tool("structure_resume_heuristic", text=raw_text)
    await acp.record_task(
        db,
        workflow=workflow,
        task_type="structure_heuristic",
        agent_name="resume_structure_agent",
        payload={},
        result={"parser": (heuristic_res.result or {}).get("parser")},
        status="completed" if heuristic_res.status == "SUCCESS" else "failed",
        error=(heuristic_res.error or {}).get("message") if heuristic_res.error else None,
    )
    task_log.append({"step": "structure_heuristic", "status": heuristic_res.status})
    if heuristic_res.status != "SUCCESS":
        return AcpWorkflowResult(
            status="failed",
            error=(heuristic_res.error or {}).get("message") or "Heuristic structure failed.",
            tasks=task_log,
        )
    heuristic = (heuristic_res.result or {}).get("content") or {}
    parser_name = str((heuristic_res.result or {}).get("parser") or "heuristic_v2")
    parser_error: str | None = None
    content = heuristic

    # 4) Optional AI
    if settings.resume_ai_enabled and settings.resume_ai_api_base.strip():
        ai_res = await call_resume_tool("structure_resume_ai", text=raw_text)
        await acp.record_task(
            db,
            workflow=workflow,
            task_type="structure_ai",
            agent_name="resume_ai_agent",
            payload={},
            result={"parser": (ai_res.result or {}).get("parser")},
            status="completed" if ai_res.status == "SUCCESS" else "failed",
            error=(ai_res.error or {}).get("message") if ai_res.error else None,
            model=settings.resume_ai_model,
        )
        task_log.append({"step": "structure_ai", "status": ai_res.status})
        if ai_res.status == "SUCCESS":
            content = _merge_resume_content((ai_res.result or {}).get("content") or {}, heuristic)
            parser_name = str((ai_res.result or {}).get("parser") or parser_name)
        else:
            parser_error = (ai_res.error or {}).get("message")
            if not settings.resume_ai_fallback_heuristic:
                return AcpWorkflowResult(
                    status="failed",
                    error=parser_error or "AI parse failed.",
                    tasks=task_log,
                )
            parser_name = "heuristic_v2_fallback"

    # 5) Validate
    validate = await call_resume_tool("validate_resume_json", content=content)
    await acp.record_task(
        db,
        workflow=workflow,
        task_type="validate",
        agent_name="resume_validate_agent",
        payload={},
        result={
            "confidence": (validate.result or {}).get("confidence"),
            "needs_review": (validate.result or {}).get("needs_review"),
        },
        status="completed" if validate.status == "SUCCESS" else "failed",
        error=(validate.error or {}).get("message") if validate.error else None,
    )
    task_log.append({"step": "validate", "status": validate.status})
    if validate.status != "SUCCESS":
        return AcpWorkflowResult(
            status="failed",
            error=(validate.error or {}).get("message") or "Validation failed.",
            tasks=task_log,
        )

    validated = validate.result or {}
    final_content = validated.get("content") or content
    needs_review = bool(validated.get("needs_review"))
    status = "needs_review" if needs_review else "completed"

    return AcpWorkflowResult(
        status=status,
        output={
            "content": final_content,
            "parser": parser_name,
            "parser_error": parser_error,
            "raw_text_chars": len(raw_text),
            "confidence": validated.get("confidence"),
            "needs_review": needs_review,
            "content_checksum": validated.get("content_checksum"),
            "sections_order": (segment.result or {}).get("order") if segment.status == "SUCCESS" else [],
            "resume_id": input_payload.get("resume_id"),
        },
        tasks=task_log,
    )


async def start_resume_parse(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
    source_bytes: bytes,
    mime_type: str,
    correlation_id: str | None = None,
) -> tuple[Workflow, AcpWorkflowResult]:
    """Public entry used by the resume domain service."""
    return await acp.start(
        db,
        user_id=user_id,
        workflow_type=WORKFLOW_TYPE,
        input_payload={
            "resume_id": str(resume_id),
            "mime_type": mime_type,
            "data_b64": base64.b64encode(source_bytes).decode("ascii"),
        },
        correlation_id=correlation_id,
    )


# Register on import
acp.register(WORKFLOW_TYPE, run_resume_parse_workflow)
