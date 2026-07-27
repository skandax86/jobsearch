"""Identity domain service — register, login, logout, session validation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from careerpilot.config import settings
from careerpilot.domains.candidate.models import CandidateProfile
from careerpilot.domains.identity.models import Session, User
from careerpilot.domains.identity.passwords import hash_password, verify_password
from careerpilot.domains.identity.tokens import generate_session_token, hash_session_token
from careerpilot.redis_client import (
    cache_session,
    get_cached_session,
    invalidate_cached_session,
)


class AuthError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class AuthResult:
    user: User
    candidate_profile: CandidateProfile
    access_token: str
    expires_at: datetime


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def register_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    display_name: str | None,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> AuthResult:
    normalized = normalize_email(email)
    existing = await db.scalar(select(User).where(User.email == normalized))
    if existing is not None:
        raise AuthError("email_taken", "An account with this email already exists.")

    user = User(
        email=normalized,
        password_hash=hash_password(password),
        display_name=display_name.strip() if display_name else None,
        status="active",
    )
    profile = CandidateProfile(user=user)
    db.add(user)
    db.add(profile)

    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise AuthError("email_taken", "An account with this email already exists.") from exc

    return await _issue_session(
        db,
        user=user,
        candidate_profile=profile,
        user_agent=user_agent,
        ip_address=ip_address,
    )


async def login_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> AuthResult:
    normalized = normalize_email(email)
    user = await db.scalar(
        select(User).where(User.email == normalized).options(selectinload(User.candidate_profile))
    )
    if user is None or not user.password_hash or not verify_password(password, user.password_hash):
        raise AuthError("invalid_credentials", "Invalid email or password.")
    if user.status != "active":
        raise AuthError("account_inactive", "This account is not active.")

    profile = user.candidate_profile
    if profile is None:
        profile = CandidateProfile(user=user)
        db.add(profile)
        await db.flush()

    return await _issue_session(
        db,
        user=user,
        candidate_profile=profile,
        user_agent=user_agent,
        ip_address=ip_address,
    )


async def logout_session(db: AsyncSession, *, token: str) -> None:
    token_hash = hash_session_token(token)
    session = await db.scalar(select(Session).where(Session.refresh_token_hash == token_hash))
    if session is None:
        await invalidate_cached_session(token_hash)
        return
    if session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)
        await db.flush()
    await invalidate_cached_session(token_hash)


async def resolve_user_from_token(db: AsyncSession, token: str) -> User | None:
    token_hash = hash_session_token(token)
    now = datetime.now(UTC)

    cached = await get_cached_session(token_hash)
    if cached:
        user_id = cached.get("user_id")
        session_id = cached.get("session_id")
        if user_id and session_id:
            user = await db.scalar(
                select(User)
                .where(User.id == uuid.UUID(user_id))
                .options(selectinload(User.candidate_profile))
            )
            if user is not None and user.status == "active":
                session = await db.scalar(
                    select(Session).where(
                        Session.id == uuid.UUID(session_id),
                        Session.revoked_at.is_(None),
                        Session.expires_at > now,
                    )
                )
                if session is not None:
                    return user
            await invalidate_cached_session(token_hash)

    session = await db.scalar(
        select(Session)
        .where(
            Session.refresh_token_hash == token_hash,
            Session.revoked_at.is_(None),
            Session.expires_at > now,
        )
        .options(selectinload(Session.user).selectinload(User.candidate_profile))
    )
    if session is None or session.user.status != "active":
        return None

    ttl = max(int((session.expires_at - now).total_seconds()), 1)
    await cache_session(
        token_hash,
        user_id=str(session.user_id),
        session_id=str(session.id),
        ttl_seconds=ttl,
    )
    return session.user


async def _issue_session(
    db: AsyncSession,
    *,
    user: User,
    candidate_profile: CandidateProfile,
    user_agent: str | None,
    ip_address: str | None,
) -> AuthResult:
    token = generate_session_token()
    token_hash = hash_session_token(token)
    expires_at = datetime.now(UTC) + timedelta(days=settings.session_ttl_days)

    session = Session(
        user_id=user.id,
        refresh_token_hash=token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(session)
    await db.flush()

    ttl = settings.session_ttl_days * 24 * 60 * 60
    await cache_session(
        token_hash,
        user_id=str(user.id),
        session_id=str(session.id),
        ttl_seconds=ttl,
    )

    await db.commit()
    await db.refresh(user)
    await db.refresh(candidate_profile)

    return AuthResult(
        user=user,
        candidate_profile=candidate_profile,
        access_token=token,
        expires_at=expires_at,
    )
