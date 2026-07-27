"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.db.session import get_db
from careerpilot.domains.identity.models import User
from careerpilot.domains.identity.service import resolve_user_from_token

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value:
        return None
    return value.strip()


async def get_current_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
    careerpilot_session: Annotated[str | None, Cookie()] = None,
) -> User:
    token = _extract_bearer(authorization) or careerpilot_session
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await resolve_user_from_token(db, token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_optional_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
    careerpilot_session: Annotated[str | None, Cookie()] = None,
) -> User | None:
    token = _extract_bearer(authorization) or careerpilot_session
    if not token:
        return None
    return await resolve_user_from_token(db, token)


OptionalUser = Annotated[User | None, Depends(get_optional_user)]
