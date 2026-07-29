"""Tests for resume MCP tools and ACP resume_parse workflow registration."""

from __future__ import annotations

import base64
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from careerpilot.acp.orchestrator import acp
from careerpilot.acp.workflows import resume_parse as resume_parse_workflow
from careerpilot.mcp.resume.server import call_resume_tool, resume_mcp


BHARATH = """
Bharath G M
Software Engineer - Data Platform
+91 89714 50169 | skanda70180@gmail.com | Bangalore, IN | linkedin.com/in/bharathx86

PROFESSIONAL OVERVIEW
GCP Certified Data Engineer expert in BigQuery and CDC architecture.
WORK EXPERIENCE
Associate Software Engineer | Epsilon, Bangalore FEB 2024 – PRESENT
● Designed production-grade GCP ETL/ELT pipelines.
Frontend Developer Intern | Technotharanga Solutions Pvt. Ltd. , Tumkur OCT 2022 – FEB 2023
● Built web interfaces using Node.js.
PROJECTS
Tracky | Personal Production Analytics Platform FEB 2024 – PRESENT
● Architected a full-stack analytics platform.
EDUCATION
Master of Computer Applications | R V College of Engineering, Bangalore Sep 2024 | 8.75 CGPA
SKILLS
Data Engineering: BigQuery, PostgreSQL, PySpark
Languages: Python, SQL
CERTIFICATIONS
GCP Professional Data Engineer | Terraform Associate
"""


def test_resume_mcp_lists_expected_tools():
    names = {t["name"] for t in resume_mcp.list_tools()}
    assert names >= {
        "extract_resume_text",
        "segment_resume_sections",
        "structure_resume_heuristic",
        "structure_resume_ai",
        "validate_resume_json",
    }


@pytest.mark.asyncio
async def test_segment_and_heuristic_mcp_tools():
    segment = await call_resume_tool("segment_resume_sections", text=BHARATH)
    assert segment.status == "SUCCESS"
    assert "experience" in (segment.result or {}).get("order", [])

    structured = await call_resume_tool("structure_resume_heuristic", text=BHARATH)
    assert structured.status == "SUCCESS"
    content = (structured.result or {}).get("content") or {}
    assert content["contact"]["name"] == "Bharath G M"
    assert len(content["experience"]) == 2

    validated = await call_resume_tool("validate_resume_json", content=content)
    assert validated.status == "SUCCESS"
    assert (validated.result or {}).get("confidence", 0) >= 0.8


@pytest.mark.asyncio
async def test_extract_resume_text_mcp_rejects_bad_mime():
    payload = base64.b64encode(b"not-a-pdf").decode("ascii")
    result = await call_resume_tool(
        "extract_resume_text",
        mime_type="application/octet-stream",
        data_b64=payload,
    )
    assert result.status == "ERROR"
    assert (result.error or {}).get("code") == "extract_failed"


def test_acp_resume_parse_workflow_registered():
    # Import side-effect registers the workflow.
    assert resume_parse_workflow.WORKFLOW_TYPE in acp.list_workflows()


@pytest.mark.asyncio
async def test_acp_resume_parse_workflow_runs_with_mocks(monkeypatch):
    async def fake_call(tool_name: str, **kwargs):
        from careerpilot.mcp.base import McpToolResult

        if tool_name == "extract_resume_text":
            return McpToolResult(status="SUCCESS", result={"text": BHARATH, "char_count": len(BHARATH)})
        if tool_name == "segment_resume_sections":
            return McpToolResult(status="SUCCESS", result={"order": ["header", "experience"]})
        if tool_name == "structure_resume_heuristic":
            return await resume_mcp.call("structure_resume_heuristic", text=BHARATH)
        if tool_name == "validate_resume_json":
            return await resume_mcp.call("validate_resume_json", content=kwargs.get("content") or {})
        return McpToolResult(status="ERROR", error={"code": "unexpected", "message": tool_name})

    monkeypatch.setattr(resume_parse_workflow, "call_resume_tool", fake_call)
    monkeypatch.setattr(resume_parse_workflow.settings, "resume_ai_enabled", False)

    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()

    class _WF:
        id = uuid.uuid4()
        state: dict = {"steps": []}

    result = await resume_parse_workflow.run_resume_parse_workflow(
        db,
        workflow=_WF(),  # type: ignore[arg-type]
        input_payload={
            "mime_type": "application/pdf",
            "data_b64": base64.b64encode(b"%PDF").decode("ascii"),
            "resume_id": str(uuid.uuid4()),
        },
    )
    assert result.status in {"completed", "needs_review"}
    assert result.output.get("content")
    assert result.output.get("parser") == "heuristic_v2"
    assert any(t["step"] == "extract_text" for t in result.tasks)
