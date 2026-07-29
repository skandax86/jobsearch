"""Resume routes — upload, parse, list, get, tailor."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from careerpilot.api.deps import CurrentUser
from careerpilot.db.session import get_db
from careerpilot.domains.jobs.service import JobError, get_job, ingest_linkedin_job_url
from careerpilot.domains.resume.schemas import (
    ApiResponse,
    CoverLetterData,
    CoverLetterRequest,
    ResumeListData,
    SaveResumeRequest,
    TailorResumeData,
    TailorResumeRequest,
    TailorSuggestion,
    UpdateResumeRequest,
    resume_to_public,
)
from careerpilot.domains.resume.service import (
    ORIGIN_GENERATED,
    ORIGIN_UPLOADED,
    SORT_CREATED,
    SORT_UPDATED,
    ResumeError,
    delete_resume,
    get_resume,
    get_resume_content,
    list_resumes,
    parse_resume_for_user,
    parse_resume_job,
    save_generated_resume,
    update_resume,
    upload_resume,
)
from careerpilot.domains.resume.tailor import (
    apply_suggestions,
    generate_cover_letter,
    suggest_resume_tailoring,
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
async def list_my_resumes(
    user: CurrentUser,
    db: DbSession,
    origin: str | None = None,
    sort: str = SORT_CREATED,
    order: str = "desc",
) -> ApiResponse:
    origin_filter = origin if origin in (ORIGIN_UPLOADED, ORIGIN_GENERATED, "all", None) else None
    if origin_filter == "all":
        origin_filter = None
    sort_key = sort if sort in (SORT_CREATED, SORT_UPDATED) else SORT_CREATED
    order_key = order if order in ("asc", "desc") else "desc"
    try:
        resumes = await list_resumes(
            db,
            user=user,
            origin=origin_filter,
            sort=sort_key,
            order=order_key,
        )
    except ResumeError as exc:
        return ApiResponse(errors=[{"code": exc.code, "message": exc.message}])
    return ApiResponse(
        data=ResumeListData(items=[resume_to_public(r, include_content=True) for r in resumes])
    )


@router.post("/from-content", status_code=status.HTTP_201_CREATED)
async def save_resume_from_content(
    payload: SaveResumeRequest,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    try:
        resume = await save_generated_resume(
            db,
            user=user,
            title=payload.title,
            content=payload.content,
            parent_resume_id=payload.parent_resume_id,
            job_posting_id=payload.job_posting_id,
            provenance={"source": "tailor_apply"},
        )
    except ResumeError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_400_BAD_REQUEST
        )
        return _error(status_code, exc.code, exc.message)
    body = ApiResponse(data=resume_to_public(resume, include_content=True))
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body.model_dump(mode="json"))


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


@router.patch("/{resume_id}")
async def update_my_resume(
    resume_id: uuid.UUID,
    payload: UpdateResumeRequest,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    if payload.title is None and payload.content is None:
        return _error(
            status.HTTP_400_BAD_REQUEST,
            "nothing_to_update",
            "Provide title and/or content to update.",
        )
    try:
        resume = await update_resume(
            db,
            user=user,
            resume_id=resume_id,
            title=payload.title,
            content=payload.content,
        )
    except ResumeError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_400_BAD_REQUEST
        )
        return _error(status_code, exc.code, exc.message)
    body = ApiResponse(data=resume_to_public(resume, include_content=True))
    return JSONResponse(content=body.model_dump(mode="json"))


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_resume(
    resume_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    try:
        await delete_resume(db, user=user, resume_id=resume_id)
    except ResumeError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_400_BAD_REQUEST
        )
        return _error(status_code, exc.code, exc.message)
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@router.post("/{resume_id}/parse")
async def parse_my_resume(
    resume_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    try:
        resume = await parse_resume_for_user(db, user=user, resume_id=resume_id)
        resume = await get_resume(db, user=user, resume_id=resume.id)
    except ResumeError as exc:
        status_code = {
            "not_found": status.HTTP_404_NOT_FOUND,
            "parse_failed": status.HTTP_422_UNPROCESSABLE_ENTITY,
        }.get(exc.code, status.HTTP_400_BAD_REQUEST)
        return _error(status_code, exc.code, exc.message)

    body = ApiResponse(data=resume_to_public(resume, include_content=True))
    return JSONResponse(content=body.model_dump(mode="json"))


@router.post("/{resume_id}/tailor")
async def tailor_my_resume(
    resume_id: uuid.UUID,
    payload: TailorResumeRequest,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    try:
        resume = await get_resume(db, user=user, resume_id=resume_id)
        content = await get_resume_content(db, user=user, resume_id=resume_id)
    except ResumeError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_400_BAD_REQUEST
        )
        return _error(status_code, exc.code, exc.message)

    if not content:
        return _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "content_missing",
            "Resume has no parsed content yet. Wait for parsing or re-parse first.",
        )

    job_posting_id = payload.job_posting_id
    if job_posting_id is None and payload.job_url:
        try:
            ingested = await ingest_linkedin_job_url(
                db,
                url=payload.job_url,
                description_override=payload.description_override,
            )
            job_posting_id = ingested["job"].id
        except JobError as exc:
            code = {
                "invalid_url": status.HTTP_400_BAD_REQUEST,
                "fetch_failed": status.HTTP_502_BAD_GATEWAY,
            }.get(exc.code, status.HTTP_400_BAD_REQUEST)
            return _error(code, exc.code, exc.message)
    elif job_posting_id is None:
        return _error(
            status.HTTP_400_BAD_REQUEST,
            "job_required",
            "Provide job_posting_id or a LinkedIn job_url.",
        )

    try:
        job = await get_job(db, job_id=job_posting_id)
    except JobError as exc:
        return _error(status.HTTP_404_NOT_FOUND, exc.code, exc.message)

    requirements = job.requirements if isinstance(job.requirements, dict) else {}

    result = suggest_resume_tailoring(
        resume_content=content,
        job_title=job.title,
        job_description=job.description or payload.description_override,
        job_requirements=requirements,
        company_name=job.company.name if job.company else None,
    )

    applied = None
    if payload.selected_suggestion_ids is not None:
        applied = apply_suggestions(
            result["current_content"],
            result["suggestions"],
            selected_ids=payload.selected_suggestion_ids,
        )

    body = ApiResponse(
        data=TailorResumeData(
            model_version=result["model_version"],
            resume_id=resume.id,
            job_posting_id=job.id,
            job_title=job.title,
            job_company=job.company.name if job.company else None,
            job_url=job.canonical_url,
            match_preview=result["match_preview"],
            suggestions=[TailorSuggestion(**s) for s in result["suggestions"]],
            current_content=result["current_content"],
            proposed_content=result["proposed_content"],
            applied_content=applied,
        )
    )
    return JSONResponse(content=body.model_dump(mode="json"))


async def _resolve_job_for_resume_action(
    db: DbSession,
    *,
    job_posting_id: uuid.UUID | None,
    job_url: str | None,
    description_override: str | None,
):
    if job_posting_id is None and job_url:
        try:
            ingested = await ingest_linkedin_job_url(
                db,
                url=job_url,
                description_override=description_override,
            )
            return ingested["job"], None
        except JobError as exc:
            return None, exc
    if job_posting_id is None:
        return None, JobError(
            "job_required",
            "Provide job_posting_id or a LinkedIn job_url.",
        )
    try:
        return await get_job(db, job_id=job_posting_id), None
    except JobError as exc:
        return None, exc


@router.post("/{resume_id}/cover-letter")
async def cover_letter_for_resume(
    resume_id: uuid.UUID,
    payload: CoverLetterRequest,
    user: CurrentUser,
    db: DbSession,
) -> JSONResponse:
    try:
        resume = await get_resume(db, user=user, resume_id=resume_id)
        content = await get_resume_content(db, user=user, resume_id=resume_id)
    except ResumeError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_400_BAD_REQUEST
        )
        return _error(status_code, exc.code, exc.message)

    if not content:
        return _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "content_missing",
            "Resume has no parsed content yet. Wait for parsing or re-parse first.",
        )

    job, job_error = await _resolve_job_for_resume_action(
        db,
        job_posting_id=payload.job_posting_id,
        job_url=payload.job_url,
        description_override=payload.description_override,
    )
    if job_error is not None:
        code = {
            "invalid_url": status.HTTP_400_BAD_REQUEST,
            "fetch_failed": status.HTTP_502_BAD_GATEWAY,
            "not_found": status.HTTP_404_NOT_FOUND,
            "job_required": status.HTTP_400_BAD_REQUEST,
        }.get(job_error.code, status.HTTP_400_BAD_REQUEST)
        return _error(code, job_error.code, job_error.message)

    requirements = job.requirements if isinstance(job.requirements, dict) else {}
    result = generate_cover_letter(
        resume_content=content,
        job_title=job.title,
        job_description=job.description or payload.description_override,
        job_requirements=requirements,
        company_name=job.company.name if job.company else None,
    )
    body = ApiResponse(
        data=CoverLetterData(
            model_version=result["model_version"],
            resume_id=resume.id,
            job_posting_id=job.id,
            job_title=job.title,
            job_company=job.company.name if job.company else None,
            job_url=job.canonical_url,
            tone=result["tone"],
            recipient=result["recipient"],
            subject=result["subject"],
            text=result["text"],
            highlights=result["highlights"],
        )
    )
    return JSONResponse(content=body.model_dump(mode="json"))
