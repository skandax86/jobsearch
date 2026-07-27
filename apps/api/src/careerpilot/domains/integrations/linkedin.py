"""LinkedIn OAuth + IntegrationConnection management."""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careerpilot.config import settings
from careerpilot.domains.candidate.models import CandidateProfile
from careerpilot.domains.identity.models import IntegrationConnection, User
from careerpilot.domains.integrations.oauth_state import pop_oauth_state, save_oauth_state
from careerpilot.security.credentials import decrypt_json, encrypt_json

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

PROVIDER = "linkedin"


class LinkedInError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def linkedin_status() -> dict[str, Any]:
    return {
        "enabled": settings.linkedin_enabled,
        "mock": settings.linkedin_mock_enabled,
        "scopes": settings.linkedin_scope_list,
        "redirect_uri": settings.linkedin_redirect_uri,
    }


async def build_authorize_url(
    *,
    intent: str,
    user_id: uuid.UUID | None = None,
) -> str:
    if intent != "connect":
        raise LinkedInError(
            "invalid_intent",
            "LinkedIn is connect-only (personal integration), not SSO login.",
        )
    if user_id is None:
        raise LinkedInError("auth_required", "Sign in before connecting LinkedIn.")
    if not settings.linkedin_enabled:
        raise LinkedInError(
            "not_configured",
            "LinkedIn OAuth is not configured. "
            "Set LINKEDIN_CLIENT_ID/SECRET or LINKEDIN_MOCK=true.",
        )

    state = secrets.token_urlsafe(32)
    await save_oauth_state(
        state,
        {
            "intent": "connect",
            "user_id": str(user_id),
            "created_at": datetime.now(UTC).isoformat(),
        },
    )

    if settings.linkedin_mock_enabled:
        query = urlencode({"code": "mock-linkedin-code", "state": state})
        # Relative URL so Next.js rewrite + test client both work.
        return f"/api/v1/auth/linkedin/callback?{query}"

    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings._linkedin_client_id_effective(),
            "redirect_uri": settings.linkedin_redirect_uri,
            "state": state,
            "scope": " ".join(settings.linkedin_scope_list),
        }
    )
    return f"{LINKEDIN_AUTH_URL}?{query}"


async def _exchange_code(code: str) -> dict[str, Any]:
    if settings.linkedin_mock_enabled and code.startswith("mock-"):
        return {
            "access_token": f"mock-access-{secrets.token_hex(8)}",
            "expires_in": 3600,
            "id_token": None,
            "scope": " ".join(settings.linkedin_scope_list),
        }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            LINKEDIN_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.linkedin_redirect_uri,
                "client_id": settings._linkedin_client_id_effective(),
                "client_secret": settings._linkedin_client_secret_effective(),
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if response.status_code >= 400:
        raise LinkedInError("token_exchange_failed", "LinkedIn token exchange failed.")
    payload = response.json()
    if "access_token" not in payload:
        raise LinkedInError("token_exchange_failed", "LinkedIn did not return an access token.")
    return payload


async def _fetch_userinfo(access_token: str) -> dict[str, Any]:
    if settings.linkedin_mock_enabled and access_token.startswith("mock-"):
        return {
            "sub": "mock-linkedin-user",
            "email": "linkedin.mock@example.com",
            "email_verified": True,
            "name": "LinkedIn Mock User",
            "given_name": "LinkedIn",
            "family_name": "Mock",
            "picture": None,
        }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            LINKEDIN_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if response.status_code >= 400:
        raise LinkedInError("userinfo_failed", "Failed to fetch LinkedIn profile.")
    data = response.json()
    if not data.get("email"):
        raise LinkedInError("email_required", "LinkedIn account email is required.")
    return data


async def _upsert_connection(
    db: AsyncSession,
    *,
    user: User,
    userinfo: dict[str, Any],
    token_payload: dict[str, Any],
) -> IntegrationConnection:
    external_id = str(userinfo.get("sub") or "")
    expires_in = int(token_payload.get("expires_in") or 3600)
    expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
    scopes = token_payload.get("scope") or " ".join(settings.linkedin_scope_list)
    scope_list = scopes.split() if isinstance(scopes, str) else list(scopes)

    creds = encrypt_json(
        {
            "access_token": token_payload["access_token"],
            "id_token": token_payload.get("id_token"),
            "token_type": token_payload.get("token_type", "Bearer"),
            "obtained_at": datetime.now(UTC).isoformat(),
        }
    )

    connection = await db.scalar(
        select(IntegrationConnection).where(
            IntegrationConnection.user_id == user.id,
            IntegrationConnection.provider == PROVIDER,
        )
    )
    if connection is None:
        connection = IntegrationConnection(
            user_id=user.id,
            provider=PROVIDER,
            status="active",
            scopes=scope_list,
            external_account_id=external_id or None,
            credentials_ref=creds,
            last_synced_at=datetime.now(UTC),
            expires_at=expires_at,
        )
        db.add(connection)
    else:
        connection.status = "active"
        connection.scopes = scope_list
        connection.external_account_id = external_id or connection.external_account_id
        connection.credentials_ref = creds
        connection.last_synced_at = datetime.now(UTC)
        connection.expires_at = expires_at

    # Soft-enrich candidate profile from LinkedIn when empty.
    profile = user.candidate_profile
    if profile is None:
        profile = await db.scalar(
            select(CandidateProfile).where(CandidateProfile.user_id == user.id)
        )
    if profile is not None:
        name = userinfo.get("name")
        if name and not user.display_name:
            user.display_name = str(name)[:255]
        if not profile.headline and userinfo.get("name"):
            profile.headline = f"{userinfo.get('name')} (via LinkedIn)"[:255]
        profile_data = dict(profile.profile_data or {})
        profile_data["linkedin"] = {
            "sub": external_id,
            "name": userinfo.get("name"),
            "picture": userinfo.get("picture"),
            "email": userinfo.get("email"),
        }
        profile.profile_data = profile_data

    await db.flush()
    return connection


async def handle_oauth_callback(
    db: AsyncSession,
    *,
    code: str | None,
    state: str | None,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> dict[str, Any]:
    _ = user_agent, ip_address
    if not code or not state:
        raise LinkedInError("missing_params", "Missing OAuth code or state.")

    oauth_state = await pop_oauth_state(state)
    if oauth_state is None:
        raise LinkedInError("invalid_state", "OAuth state is invalid or expired.")

    if oauth_state.get("intent") != "connect":
        raise LinkedInError(
            "invalid_intent",
            "LinkedIn is connect-only (personal integration), not SSO login.",
        )

    user_id_raw = oauth_state.get("user_id")
    if not user_id_raw:
        raise LinkedInError("auth_required", "Connect requires an authenticated session.")

    token_payload = await _exchange_code(code)
    userinfo = await _fetch_userinfo(token_payload["access_token"])

    user = await db.scalar(
        select(User)
        .where(User.id == uuid.UUID(user_id_raw))
        .options(selectinload(User.candidate_profile))
    )
    if user is None:
        raise LinkedInError("user_not_found", "User not found for LinkedIn connect.")

    await _upsert_connection(db, user=user, userinfo=userinfo, token_payload=token_payload)
    await db.commit()
    return {
        "intent": "connect",
        "redirect_url": f"{settings.web_app_url}/dashboard?linkedin=connected",
    }


async def get_linkedin_connection(db: AsyncSession, *, user: User) -> IntegrationConnection | None:
    return await db.scalar(
        select(IntegrationConnection).where(
            IntegrationConnection.user_id == user.id,
            IntegrationConnection.provider == PROVIDER,
        )
    )


async def disconnect_linkedin(db: AsyncSession, *, user: User) -> None:
    connection = await get_linkedin_connection(db, user=user)
    if connection is None:
        raise LinkedInError("not_connected", "LinkedIn is not connected.")
    connection.status = "revoked"
    connection.credentials_ref = None
    connection.expires_at = datetime.now(UTC)
    await db.commit()


def load_access_token(connection: IntegrationConnection) -> str | None:
    if not connection.credentials_ref or connection.status != "active":
        return None
    if connection.expires_at and connection.expires_at < datetime.now(UTC):
        return None
    try:
        payload = decrypt_json(connection.credentials_ref)
    except Exception:
        return None
    token = payload.get("access_token")
    return str(token) if token else None


async def list_integrations(db: AsyncSession, *, user: User) -> list[dict[str, Any]]:
    rows = list(
        await db.scalars(
            select(IntegrationConnection).where(IntegrationConnection.user_id == user.id)
        )
    )
    return [
        {
            "provider": row.provider,
            "status": row.status,
            "scopes": row.scopes,
            "external_account_id": row.external_account_id,
            "last_synced_at": row.last_synced_at,
            "expires_at": row.expires_at,
            "connected": row.status == "active" and bool(row.credentials_ref),
        }
        for row in rows
    ]
