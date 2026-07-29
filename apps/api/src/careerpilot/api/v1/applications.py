"""Application tracker routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.api.deps import CurrentUser
from careerpilot.db.session import get_db
from careerpilot.domains.applications.schemas import (
    ApplicationCreate,
    ApplicationPublic,
    ApplicationStatusUpdate,
)
from careerpilot.domains.applications.service import (
    ApplicationError,
    delete_application,
    list_applications,
    update_application_status,
    upsert_application,
)
from careerpilot.domains.identity.schemas import ApiResponse

router = APIRouter(prefix="/applications", tags=["applications"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("")
async def list_my_applications(user: CurrentUser, db: DbSession) -> JSONResponse:
    items = await list_applications(db, user=user)
    public = [ApplicationPublic.model_validate(item).model_dump(mode="json") for item in items]
    return JSONResponse(content=ApiResponse(data={"items": public, "total": len(public)}).model_dump())


@router.post("")
async def create_or_upsert_application(
    payload: ApplicationCreate,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    try:
        item = await upsert_application(
            db,
            user=user,
            job_posting_id=payload.job_posting_id,
            status=payload.status,
            idempotency_key=payload.idempotency_key,
        )
        await db.commit()
    except ApplicationError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND
            if exc.code in {"job_not_found", "profile_missing"}
            else status.HTTP_400_BAD_REQUEST,
            content=ApiResponse(errors=[{"code": exc.code, "message": exc.message}]).model_dump(),
        )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=ApiResponse(data=ApplicationPublic.model_validate(item).model_dump(mode="json")).model_dump(),
    )


@router.patch("/{application_id}")
async def patch_application_status(
    application_id: uuid.UUID,
    payload: ApplicationStatusUpdate,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    try:
        item = await update_application_status(
            db,
            user=user,
            application_id=application_id,
            status=payload.status,
            reason=payload.reason,
        )
        await db.commit()
    except ApplicationError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND
            if exc.code == "not_found"
            else status.HTTP_400_BAD_REQUEST,
            content=ApiResponse(errors=[{"code": exc.code, "message": exc.message}]).model_dump(),
        )
    return JSONResponse(
        content=ApiResponse(data=ApplicationPublic.model_validate(item).model_dump(mode="json")).model_dump()
    )


@router.delete("/{application_id}")
async def remove_application(
    application_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    try:
        await delete_application(db, user=user, application_id=application_id)
        await db.commit()
    except ApplicationError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND
            if exc.code == "not_found"
            else status.HTTP_400_BAD_REQUEST,
            content=ApiResponse(errors=[{"code": exc.code, "message": exc.message}]).model_dump(),
        )
    return JSONResponse(content=ApiResponse(data={"ok": True}).model_dump())
