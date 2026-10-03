"""Resume upload and management endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.domain.skills import parse_json_list
from app.models.resume import Resume
from app.services.resume_parser import ResumeParser

router = APIRouter(prefix="/resumes", tags=["Resumes"])


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_url: str | None = None
    is_primary: bool
    parsed_skills: list[str] | None = None
    parsed_experience: str | None = None
    parsed_education: str | None = None
    raw_text: str | None = None
    created_at: str
    updated_at: str


class ResumeUpdate(BaseModel):
    raw_text: str | None = None
    skills: list[str] | None = None
    is_primary: bool | None = None


def _to_out(r: Resume) -> ResumeOut:
    skills = parse_json_list(r.skills)
    return ResumeOut(
        id=r.id,
        filename=r.filename,
        file_url=f"/uploads/{Path(r.file_path).name}" if r.file_path else None,
        is_primary=r.is_primary,
        parsed_skills=skills or None,
        parsed_experience=str(r.experience_years) if r.experience_years is not None else None,
        parsed_education=r.education,
        raw_text=r.raw_text,
        created_at=r.created_at.isoformat() if r.created_at else "",
        updated_at=r.updated_at.isoformat() if r.updated_at else "",
    )


@router.get("", response_model=list[ResumeOut])
async def list_resumes(user: CurrentUser, db: DbSession) -> list[ResumeOut]:
    result = await db.execute(
        select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())
    )
    return [_to_out(r) for r in result.scalars().all()]


@router.post("/upload", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> ResumeOut:
    settings = get_settings()
    suffix = Path(file.filename or "resume.pdf").suffix.lower()
    if suffix not in ResumeParser.supported:
        raise HTTPException(400, detail="Only PDF, DOCX, and TXT are supported")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4()}{suffix}"
    dest = upload_dir / stored_name
    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(400, detail="File too large")
    dest.write_bytes(content)

    try:
        parsed = ResumeParser().parse_file(dest)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(400, detail=f"Parse failed: {exc}") from exc

    # First resume becomes primary
    existing = await db.execute(select(Resume.id).where(Resume.user_id == user.id).limit(1))
    is_primary = existing.scalar_one_or_none() is None

    resume = Resume(
        user_id=user.id,
        filename=file.filename or stored_name,
        file_path=str(dest),
        content_type=file.content_type or "application/octet-stream",
        raw_text=parsed["raw_text"],
        parsed_json=parsed["parsed_json"],
        skills=json.dumps(parsed["skills"]),
        technologies=json.dumps(parsed["technologies"]),
        experience_years=parsed["experience_years"],
        education=parsed["education"] or None,
        projects=parsed["projects"] or None,
        certifications=json.dumps(parsed["certifications"]) if parsed["certifications"] else None,
        languages=json.dumps(parsed["languages"]),
        is_primary=is_primary,
    )
    db.add(resume)
    await db.flush()
    await db.refresh(resume)
    return _to_out(resume)


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(resume_id: str, user: CurrentUser, db: DbSession) -> ResumeOut:
    resume = await _get_owned(db, user.id, resume_id)
    return _to_out(resume)


@router.patch("/{resume_id}", response_model=ResumeOut)
async def update_resume(
    resume_id: str, data: ResumeUpdate, user: CurrentUser, db: DbSession
) -> ResumeOut:
    resume = await _get_owned(db, user.id, resume_id)
    if data.raw_text is not None:
        resume.raw_text = data.raw_text
    if data.skills is not None:
        resume.skills = json.dumps(data.skills)
    if data.is_primary is True:
        await db.execute(
            update(Resume).where(Resume.user_id == user.id).values(is_primary=False)
        )
        resume.is_primary = True
    await db.flush()
    await db.refresh(resume)
    return _to_out(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_resume(resume_id: str, user: CurrentUser, db: DbSession) -> Response:
    resume = await _get_owned(db, user.id, resume_id)
    Path(resume.file_path).unlink(missing_ok=True)
    await db.delete(resume)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{resume_id}/set-primary", response_model=ResumeOut)
async def set_primary(resume_id: str, user: CurrentUser, db: DbSession) -> ResumeOut:
    resume = await _get_owned(db, user.id, resume_id)
    await db.execute(update(Resume).where(Resume.user_id == user.id).values(is_primary=False))
    resume.is_primary = True
    await db.flush()
    await db.refresh(resume)
    return _to_out(resume)


async def _get_owned(db, user_id: str, resume_id: str) -> Resume:
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    )
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(404, detail="Resume not found")
    return resume
