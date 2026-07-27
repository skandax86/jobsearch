"""Auth routes — register, login, logout."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.config import settings
from careerpilot.db.session import get_db
from careerpilot.domains.identity.schemas import (
    ApiResponse,
    AuthData,
    CandidateProfilePublic,
    LoginRequest,
    RegisterRequest,
    UserPublic,
)
from careerpilot.domains.identity.service import (
    AuthError,
    login_user,
    logout_session,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return user_agent, ip


def _set_session_cookie(response: Response, token: str, expires_at: datetime) -> None:
    max_age = max(int((expires_at - datetime.now(UTC)).total_seconds()), 0)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.app_env != "development",
        samesite="lax",
        max_age=max_age,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.session_cookie_name, path="/")


def _auth_payload(result) -> dict:
    body = ApiResponse(
        data=AuthData(
            access_token=result.access_token,
            expires_at=result.expires_at,
            user=UserPublic.model_validate(result.user),
            candidate_profile=CandidateProfilePublic.model_validate(result.candidate_profile),
        )
    )
    return body.model_dump(mode="json")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request, db: DbSession) -> JSONResponse:
    user_agent, ip = _client_meta(request)
    try:
        result = await register_user(
            db,
            email=str(payload.email),
            password=payload.password,
            display_name=payload.display_name,
            user_agent=user_agent,
            ip_address=ip,
        )
    except AuthError as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT
            if exc.code == "email_taken"
            else status.HTTP_400_BAD_REQUEST,
            content=ApiResponse(errors=[{"code": exc.code, "message": exc.message}]).model_dump(),
        )

    response = JSONResponse(status_code=status.HTTP_201_CREATED, content=_auth_payload(result))
    _set_session_cookie(response, result.access_token, result.expires_at)
    return response


@router.post("/login")
async def login(payload: LoginRequest, request: Request, db: DbSession) -> JSONResponse:
    user_agent, ip = _client_meta(request)
    try:
        result = await login_user(
            db,
            email=str(payload.email),
            password=payload.password,
            user_agent=user_agent,
            ip_address=ip,
        )
    except AuthError as exc:
        code = (
            status.HTTP_403_FORBIDDEN
            if exc.code == "account_inactive"
            else status.HTTP_401_UNAUTHORIZED
        )
        return JSONResponse(
            status_code=code,
            content=ApiResponse(errors=[{"code": exc.code, "message": exc.message}]).model_dump(),
        )

    response = JSONResponse(content=_auth_payload(result))
    _set_session_cookie(response, result.access_token, result.expires_at)
    return response


@router.post("/logout")
async def logout(request: Request, db: DbSession) -> JSONResponse:
    auth = request.headers.get("authorization")
    token = None
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
    if not token:
        token = request.cookies.get(settings.session_cookie_name)

    if token:
        await logout_session(db, token=token)
        await db.commit()

    response = JSONResponse(content=ApiResponse(data={"ok": True}).model_dump())
    _clear_session_cookie(response)
    return response
