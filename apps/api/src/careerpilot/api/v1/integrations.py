"""Integrations routes — list / disconnect providers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.api.deps import CurrentUser
from careerpilot.db.session import get_db
from careerpilot.domains.identity.schemas import ApiResponse
from careerpilot.domains.integrations.linkedin import (
    LinkedInError,
    disconnect_linkedin,
    list_integrations,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("")
async def list_my_integrations(user: CurrentUser, db: DbSession) -> JSONResponse:
    items = await list_integrations(db, user=user)
    return JSONResponse(content=ApiResponse(data={"items": items}).model_dump(mode="json"))


@router.delete("/linkedin")
async def disconnect(user: CurrentUser, db: DbSession) -> JSONResponse:
    try:
        await disconnect_linkedin(db, user=user)
    except LinkedInError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND
            if exc.code == "not_connected"
            else status.HTTP_400_BAD_REQUEST,
            content=ApiResponse(errors=[{"code": exc.code, "message": exc.message}]).model_dump(),
        )
    return JSONResponse(content=ApiResponse(data={"ok": True, "provider": "linkedin"}).model_dump())
