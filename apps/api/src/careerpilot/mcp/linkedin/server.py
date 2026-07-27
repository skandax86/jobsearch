"""LinkedIn MCP server — profile + connection tools (Jobs API partner-gated)."""

from __future__ import annotations

import uuid
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careerpilot.config import settings
from careerpilot.domains.identity.models import IntegrationConnection, User
from careerpilot.domains.integrations.linkedin import (
    LINKEDIN_USERINFO_URL,
    PROVIDER,
    load_access_token,
)
from careerpilot.mcp.base import McpServer, McpToolResult

linkedin_mcp = McpServer("linkedin")


async def _load_user_connection(
    db: AsyncSession, user_id: uuid.UUID
) -> tuple[User | None, IntegrationConnection | None]:
    user = await db.scalar(
        select(User).where(User.id == user_id).options(selectinload(User.candidate_profile))
    )
    if user is None:
        return None, None
    connection = await db.scalar(
        select(IntegrationConnection).where(
            IntegrationConnection.user_id == user.id,
            IntegrationConnection.provider == PROVIDER,
        )
    )
    return user, connection


@linkedin_mcp.tool(
    "linkedin_connection_status",
    "Return whether the user has an active LinkedIn OAuth connection.",
)
async def linkedin_connection_status(*, db: AsyncSession, user_id: uuid.UUID) -> McpToolResult:
    _user, connection = await _load_user_connection(db, user_id)
    if connection is None or connection.status != "active":
        return McpToolResult(
            status="SUCCESS",
            result={
                "connected": False,
                "provider": PROVIDER,
                "mock": settings.linkedin_mock_enabled,
            },
        )
    return McpToolResult(
        status="SUCCESS",
        result={
            "connected": True,
            "provider": PROVIDER,
            "external_account_id": connection.external_account_id,
            "scopes": connection.scopes,
            "expires_at": connection.expires_at.isoformat() if connection.expires_at else None,
            "mock": settings.linkedin_mock_enabled,
        },
        metadata={"tool": "linkedin_connection_status"},
    )


@linkedin_mcp.tool(
    "linkedin_get_profile",
    "Fetch the authorized LinkedIn OpenID profile (name, email, picture).",
)
async def linkedin_get_profile(*, db: AsyncSession, user_id: uuid.UUID) -> McpToolResult:
    user, connection = await _load_user_connection(db, user_id)
    if user is None:
        return McpToolResult(
            status="ERROR",
            error={"code": "user_not_found", "message": "User not found."},
        )
    if connection is None or connection.status != "active":
        return McpToolResult(
            status="ERROR",
            error={"code": "not_connected", "message": "Connect LinkedIn first."},
        )
    token = load_access_token(connection)
    if not token:
        return McpToolResult(
            status="ERROR",
            error={"code": "token_expired", "message": "LinkedIn token missing or expired."},
        )

    if settings.linkedin_mock_enabled and token.startswith("mock-"):
        profile_data = (user.candidate_profile.profile_data or {}) if user.candidate_profile else {}
        linkedin = profile_data.get("linkedin") if isinstance(profile_data, dict) else {}
        return McpToolResult(
            status="SUCCESS",
            result={
                "sub": connection.external_account_id,
                "email": user.email,
                "name": user.display_name or (linkedin or {}).get("name"),
                "picture": (linkedin or {}).get("picture"),
                "source": "mock",
            },
            metadata={"tool": "linkedin_get_profile"},
        )

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            LINKEDIN_USERINFO_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
    if response.status_code >= 400:
        return McpToolResult(
            status="ERROR",
            error={"code": "userinfo_failed", "message": "LinkedIn userinfo request failed."},
        )
    data = response.json()
    return McpToolResult(
        status="SUCCESS",
        result={
            "sub": data.get("sub"),
            "email": data.get("email"),
            "name": data.get("name"),
            "given_name": data.get("given_name"),
            "family_name": data.get("family_name"),
            "picture": data.get("picture"),
            "source": "linkedin_openid",
        },
        metadata={"tool": "linkedin_get_profile"},
    )


@linkedin_mcp.tool(
    "linkedin_search_jobs",
    "Search LinkedIn jobs (partner API required; may return UNSUPPORTED).",
)
async def linkedin_search_jobs(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str | None = None,
    limit: int = 20,
) -> McpToolResult:
    _ = db, user_id, limit
    # Partner Jobs API is not available for standard LinkedIn apps.
    return McpToolResult(
        status="UNSUPPORTED",
        result={
            "query": query,
            "jobs": [],
            "fallback": "job_discovery_providers",
            "reason": (
                "LinkedIn Jobs API requires approved partner access. "
                "Use Remotive/demo discovery providers or a future browser MCP."
            ),
        },
        metadata={"tool": "linkedin_search_jobs", "provider_policy": "partner_required"},
    )


async def call_linkedin_tool(
    db: AsyncSession,
    *,
    tool_name: str,
    user_id: uuid.UUID,
    **kwargs: Any,
) -> McpToolResult:
    return await linkedin_mcp.call(tool_name, db=db, user_id=user_id, **kwargs)
