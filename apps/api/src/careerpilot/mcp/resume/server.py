"""Resume MCP server — text extract, section split, structure, validate."""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from careerpilot.config import settings
from careerpilot.domains.resume.parser.ai_extract import (
    PARSER_VERSION as AI_PARSER_VERSION,
    AIParseError,
    ai_resume_parsing_enabled,
    structure_resume_text_with_ai,
    validate_and_repair_ai_payload,
)
from careerpilot.domains.resume.parser.extract import ExtractionError, extract_text
from careerpilot.domains.resume.parser.sections import (
    format_sections_for_prompt,
    segment_resume_text,
)
from careerpilot.domains.resume.parser.structure import structure_resume_text
from careerpilot.domains.resume.schema import normalize_resume_content
from careerpilot.mcp.base import McpServer, McpToolResult

resume_mcp = McpServer("resume")


def _decode_bytes(data_b64: str | None, data_hex: str | None = None) -> bytes:
    if data_b64:
        return base64.b64decode(data_b64)
    if data_hex:
        return bytes.fromhex(data_hex)
    raise ValueError("Provide data_b64 or data_hex.")


@resume_mcp.tool(
    "extract_resume_text",
    "Extract plain text from a PDF/DOCX resume byte payload (base64).",
)
async def extract_resume_text(
    *,
    mime_type: str,
    data_b64: str | None = None,
    data_hex: str | None = None,
) -> McpToolResult:
    try:
        data = _decode_bytes(data_b64, data_hex)
        text = extract_text(data=data, mime_type=mime_type)
    except ExtractionError as exc:
        return McpToolResult(
            status="ERROR",
            error={"code": "extract_failed", "message": exc.message},
        )
    except Exception as exc:  # noqa: BLE001
        return McpToolResult(
            status="ERROR",
            error={"code": "extract_failed", "message": str(exc) or "extract failed"},
        )
    return McpToolResult(
        status="SUCCESS",
        result={"text": text, "char_count": len(text or "")},
        metadata={"tool": "extract_resume_text", "mime_type": mime_type},
    )


@resume_mcp.tool(
    "segment_resume_sections",
    "Split resume text into HEADER / SUMMARY / EXPERIENCE / PROJECTS / EDUCATION / SKILLS / …",
)
async def segment_resume_sections(*, text: str) -> McpToolResult:
    segments = segment_resume_text(text or "")
    return McpToolResult(
        status="SUCCESS",
        result={
            "segments": segments,
            "section_prompt": format_sections_for_prompt(segments),
            "order": list(segments.get("order") or []),
        },
        metadata={"tool": "segment_resume_sections"},
    )


@resume_mcp.tool(
    "structure_resume_heuristic",
    "Rule-based ATS extract from resume text into CareerPilot resume JSON (schema 1.1).",
)
async def structure_resume_heuristic(*, text: str) -> McpToolResult:
    content = normalize_resume_content(structure_resume_text(text or ""))
    return McpToolResult(
        status="SUCCESS",
        result={"content": content, "parser": "heuristic_v2"},
        metadata={"tool": "structure_resume_heuristic"},
    )


@resume_mcp.tool(
    "structure_resume_ai",
    "AI extract (OpenAI-compatible) into CareerPilot resume JSON. Falls back only when caller merges.",
)
async def structure_resume_ai(*, text: str) -> McpToolResult:
    if not ai_resume_parsing_enabled():
        return McpToolResult(
            status="ERROR",
            error={"code": "ai_disabled", "message": "AI resume parsing is not enabled."},
        )
    try:
        content = await structure_resume_text_with_ai(text or "")
    except AIParseError as exc:
        return McpToolResult(
            status="ERROR",
            error={"code": exc.code, "message": exc.message},
        )
    return McpToolResult(
        status="SUCCESS",
        result={"content": content, "parser": AI_PARSER_VERSION},
        metadata={
            "tool": "structure_resume_ai",
            "model": settings.resume_ai_model,
        },
    )


@resume_mcp.tool(
    "validate_resume_json",
    "Validate/repair resume JSON and return confidence + review flags.",
)
async def validate_resume_json(*, content: dict[str, Any]) -> McpToolResult:
    normalized = normalize_resume_content(content if isinstance(content, dict) else {})
    # Reuse AI payload repair for section-leakage on flat shared schema via a shim.
    shim = {
        "full_name": (normalized.get("contact") or {}).get("name"),
        "email": (normalized.get("contact") or {}).get("email"),
        "phone": (normalized.get("contact") or {}).get("phone"),
        "location": (normalized.get("contact") or {}).get("location"),
        "summary": normalized.get("summary"),
        "skills": normalized.get("skills") or [],
        "languages": normalized.get("languages") or [],
        "experience": [
            {
                "job_title": e.get("title"),
                "company": e.get("company"),
                "location": e.get("location"),
                "start_date": e.get("start_date"),
                "end_date": e.get("end_date"),
                "currently_working": e.get("is_current"),
                "summary": e.get("summary"),
                "achievements": e.get("bullets") or [],
            }
            for e in (normalized.get("experience") or [])
            if isinstance(e, dict)
        ],
        "education": normalized.get("education") or [],
        "projects": [
            {
                "title": p.get("title"),
                "organization": p.get("organization"),
                "start_date": p.get("start_date"),
                "end_date": p.get("end_date"),
                "currently_working": p.get("is_current"),
                "highlights": p.get("bullets") or [],
                "technologies": p.get("technologies") or [],
            }
            for p in (normalized.get("projects") or [])
            if isinstance(p, dict)
        ],
        "certifications": [
            {
                "name": c.get("title"),
                "issuer": c.get("issuer"),
                "issue_date": c.get("date"),
                "expiry_date": c.get("expiry_date"),
                "credential_id": c.get("credential_id"),
                "credential_url": c.get("url"),
            }
            for c in (normalized.get("certifications") or [])
            if isinstance(c, dict)
        ],
        "awards": normalized.get("awards") or [],
    }
    repaired = validate_and_repair_ai_payload(shim)
    # Keep normalized as source of truth for shared schema; compute confidence.
    confidence = _confidence(normalized)
    needs_review = confidence < 0.8 or not any(
        normalized.get(k)
        for k in ("experience", "skills", "projects", "education", "summary", "headline")
    )
    checksum = hashlib.sha256(
        json.dumps(normalized, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return McpToolResult(
        status="SUCCESS",
        result={
            "content": normalized,
            "confidence": confidence,
            "needs_review": needs_review,
            "content_checksum": checksum,
            "repair_hints": {
                "skills_count": len(repaired.get("skills") or []),
                "experience_count": len(repaired.get("experience") or []),
            },
        },
        metadata={"tool": "validate_resume_json"},
    )


def _confidence(content: dict[str, Any]) -> float:
    score = 0.0
    contact = content.get("contact") or {}
    if contact.get("name"):
        score += 0.1
    if contact.get("email"):
        score += 0.1
    if content.get("headline"):
        score += 0.05
    if content.get("summary"):
        score += 0.1
    if content.get("experience"):
        score += 0.25
    if content.get("education"):
        score += 0.15
    if content.get("skills"):
        score += 0.1
    if content.get("projects"):
        score += 0.1
    if content.get("certifications"):
        score += 0.05
    return round(min(score, 1.0), 2)


async def call_resume_tool(tool_name: str, **kwargs: Any) -> McpToolResult:
    return await resume_mcp.call(tool_name, **kwargs)
