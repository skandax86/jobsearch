"""LinkedIn OAuth routes — personal Connect only (not SSO login)."""

from __future__ import annotations

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.api.deps import CurrentUser
from careerpilot.config import settings
from careerpilot.db.session import get_db
from careerpilot.domains.identity.schemas import ApiResponse
from careerpilot.domains.integrations.linkedin import (
    LinkedInError,
    build_authorize_url,
    handle_oauth_callback,
    linkedin_status,
)

router = APIRouter(prefix="/auth/linkedin", tags=["linkedin"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return user_agent, ip


@router.get("/status")
async def status_endpoint() -> JSONResponse:
    body = ApiResponse(data=linkedin_status())
    return JSONResponse(content=body.model_dump(mode="json"))


@router.get("/connect", response_model=None)
async def connect_start(
    user: CurrentUser,
    redirect: Annotated[bool, Query()] = True,
) -> RedirectResponse | JSONResponse:
    """Start personal LinkedIn connect (requires existing CareerPilot session)."""
    try:
        url = await build_authorize_url(intent="connect", user_id=user.id)
    except LinkedInError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ApiResponse(errors=[{"code": exc.code, "message": exc.message}]).model_dump(),
        )
    if redirect:
        return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
    return JSONResponse(content=ApiResponse(data={"authorize_url": url}).model_dump())


@router.get("/callback")
async def callback(
    request: Request,
    db: DbSession,
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
    error_description: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    dashboard = f"{settings.web_app_url}/dashboard"
    if error:
        query = urlencode(
            {"linkedin": "error", "message": error_description or error},
        )
        return RedirectResponse(url=f"{dashboard}?{query}", status_code=status.HTTP_302_FOUND)

    user_agent, ip = _client_meta(request)
    try:
        result = await handle_oauth_callback(
            db,
            code=code,
            state=state,
            user_agent=user_agent,
            ip_address=ip,
        )
    except LinkedInError as exc:
        code_name = getattr(exc, "code", "oauth_failed")
        message = getattr(exc, "message", str(exc))
        query = urlencode({"linkedin": "error", "message": message, "code": code_name})
        return RedirectResponse(url=f"{dashboard}?{query}", status_code=status.HTTP_302_FOUND)

    return RedirectResponse(url=result["redirect_url"], status_code=status.HTTP_302_FOUND)
