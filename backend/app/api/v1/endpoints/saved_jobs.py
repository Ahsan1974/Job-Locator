"""Saved jobs endpoints."""

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.job import Job
from app.models.saved_job import SavedJob
from app.schemas.job import JobListItem

router = APIRouter(prefix="/saved-jobs", tags=["Saved Jobs"])


class SaveJobRequest(BaseModel):
    job_id: str
    notes: str | None = None


class SavedJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    notes: str | None = None
    job: JobListItem | None = None


@router.get("", response_model=list[SavedJobResponse])
async def list_saved(user: CurrentUser, db: DbSession) -> list[SavedJobResponse]:
    result = await db.execute(
        select(SavedJob)
        .options(selectinload(SavedJob.job).selectinload(Job.company))
        .where(SavedJob.user_id == user.id)
        .order_by(SavedJob.created_at.desc())
    )
    rows = result.scalars().all()
    out: list[SavedJobResponse] = []
    for row in rows:
        item = SavedJobResponse(id=row.id, job_id=row.job_id, notes=row.notes)
        if row.job:
            item.job = JobListItem.model_validate(row.job)
        out.append(item)
    return out


@router.post("", response_model=SavedJobResponse, status_code=status.HTTP_201_CREATED)
async def save_job(data: SaveJobRequest, user: CurrentUser, db: DbSession) -> SavedJobResponse:
    job = await db.get(Job, data.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    existing = await db.execute(
        select(SavedJob).where(SavedJob.user_id == user.id, SavedJob.job_id == data.job_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Job already saved")
    row = SavedJob(user_id=user.id, job_id=data.job_id, notes=data.notes)
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return SavedJobResponse(id=row.id, job_id=row.job_id, notes=row.notes)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def unsave_job(job_id: str, user: CurrentUser, db: DbSession) -> Response:
    result = await db.execute(
        select(SavedJob).where(SavedJob.user_id == user.id, SavedJob.job_id == job_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Saved job not found")
    await db.delete(row)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
