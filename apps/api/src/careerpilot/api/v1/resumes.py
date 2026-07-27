"""Resume routes — upload, parse, list, get."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.api.deps import CurrentUser
from careerpilot.db.session import get_db
from careerpilot.domains.resume.schemas import (
    ApiResponse,
    ResumeListData,
    resume_to_public,
)
from careerpilot.domains.resume.service import (
    ResumeError,
    get_resume,
    list_resumes,
    parse_resume_for_user,
    parse_resume_job,
    upload_resume,
)

router = APIRouter(prefix="/resumes", tags=["resumes"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(errors=[{"code": code, "message": message}]).model_dump(),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_resume(
    user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
) -> JSONResponse:
    data = await file.read()
    try:
        resume = await upload_resume(
            db,
            user=user,
            filename=title or file.filename,
            content_type=file.content_type,
            data=data,
        )
    except ResumeError as exc:
        code = {
            "unsupported_type": status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "file_too_large": status.HTTP_413_CONTENT_TOO_LARGE,
            "empty_file": status.HTTP_400_BAD_REQUEST,
            "profile_missing": status.HTTP_400_BAD_REQUEST,
        }.get(exc.code, status.HTTP_400_BAD_REQUEST)
        return _error(code, exc.code, exc.message)

    background_tasks.add_task(parse_resume_job, resume.id)
    body = ApiResponse(data=resume_to_public(resume))
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body.model_dump(mode="json"))


@router.get("")
async def list_my_resumes(user: CurrentUser, db: DbSession) -> ApiResponse:
    try:
        resumes = await list_resumes(db, user=user)
    except ResumeError as exc:
        return ApiResponse(errors=[{"code": exc.code, "message": exc.message}])
    return ApiResponse(
        data=ResumeListData(items=[resume_to_public(r, include_content=True) for r in resumes])
    )


@router.get("/{resume_id}")
async def get_my_resume(
    resume_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    try:
        resume = await get_resume(db, user=user, resume_id=resume_id)
    except ResumeError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_400_BAD_REQUEST
        )
        return _error(status_code, exc.code, exc.message)
    body = ApiResponse(data=resume_to_public(resume, include_content=True))
    return JSONResponse(content=body.model_dump(mode="json"))


@router.post("/{resume_id}/parse")
async def parse_my_resume(
    resume_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    try:
        resume = await parse_resume_for_user(db, user=user, resume_id=resume_id)
        # Reload with content
        resume = await get_resume(db, user=user, resume_id=resume.id)
    except ResumeError as exc:
        status_code = {
            "not_found": status.HTTP_404_NOT_FOUND,
            "parse_failed": status.HTTP_422_UNPROCESSABLE_ENTITY,
        }.get(exc.code, status.HTTP_400_BAD_REQUEST)
        return _error(status_code, exc.code, exc.message)

    body = ApiResponse(data=resume_to_public(resume, include_content=True))
    return JSONResponse(content=body.model_dump(mode="json"))
