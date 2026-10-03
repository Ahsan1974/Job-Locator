"""Companies endpoints."""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.application import Application
from app.models.company import Company
from app.models.contact_note import ContactNote
from app.models.job import Job
from app.models.recruiter import Recruiter
from app.repositories.company_repository import CompanyRepository
from app.schemas.job import JobListItem

router = APIRouter(prefix="/companies", tags=["Companies"])


class CompanyDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    description: str | None = None
    industry: str | None = None
    company_size: str | None = None
    website: str | None = None
    logo_url: str | None = None
    headquarters_country: str | None = None
    headquarters_city: str | None = None
    technology_stack: str | None = None
    funding_info: str | None = None
    hiring_trends: str | None = None
    avg_hiring_days: int | None = None
    interview_difficulty: str | None = None
    offers_visa_sponsorship: bool | None = None
    open_positions: int = 0


class CompanyListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    logo_url: str | None = None
    industry: str | None = None
    company_size: str | None = None
    headquarters_country: str | None = None
    offers_visa_sponsorship: bool | None = None
    open_positions: int = 0


class NoteBody(BaseModel):
    note: str


@router.get("", response_model=list[CompanyListItem])
async def list_companies(
    db: DbSession,
    q: str | None = None,
    visa: bool | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[CompanyListItem]:
    stmt = select(Company).order_by(Company.name).offset(offset).limit(limit)
    if q:
        stmt = stmt.where(Company.name.ilike(f"%{q}%"))
    if visa is not None:
        stmt = stmt.where(Company.offers_visa_sponsorship.is_(visa))
    result = await db.execute(stmt)
    companies = result.scalars().all()

    items: list[CompanyListItem] = []
    for c in companies:
        count = (
            await db.execute(
                select(func.count()).select_from(Job).where(Job.company_id == c.id, Job.is_active.is_(True))
            )
        ).scalar_one()
        item = CompanyListItem.model_validate(c)
        item.open_positions = count
        items.append(item)
    return items


@router.get("/{slug}", response_model=CompanyDetail)
async def get_company(slug: str, db: DbSession) -> CompanyDetail:
    company = await CompanyRepository(db).get_by_slug(slug)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    count = (
        await db.execute(
            select(func.count())
            .select_from(Job)
            .where(Job.company_id == company.id, Job.is_active.is_(True))
        )
    ).scalar_one()
    detail = CompanyDetail.model_validate(company)
    detail.open_positions = count
    return detail


@router.get("/{slug}/jobs", response_model=list[JobListItem])
async def company_jobs(slug: str, db: DbSession) -> list[JobListItem]:
    company = await CompanyRepository(db).get_by_slug(slug)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    result = await db.execute(
        select(Job)
        .options(selectinload(Job.company))
        .where(Job.company_id == company.id, Job.is_active.is_(True))
        .order_by(Job.posted_at.desc().nullslast())
    )
    return [JobListItem.model_validate(j) for j in result.scalars().all()]


@router.get("/{slug}/workspace")
async def company_workspace(slug: str, user: CurrentUser, db: DbSession) -> dict:
    company = await CompanyRepository(db).get_by_slug(slug)
    if company is None:
        raise HTTPException(404, detail="Company not found")
    note = (
        await db.execute(
            select(ContactNote).where(
                ContactNote.user_id == user.id,
                ContactNote.company_id == company.id,
                ContactNote.recruiter_id.is_(None),
            )
        )
    ).scalar_one_or_none()
    applications = (
        await db.execute(
            select(Application, Job)
            .join(Job, Application.job_id == Job.id)
            .where(Application.user_id == user.id, Job.company_id == company.id)
            .order_by(Application.updated_at.desc())
        )
    ).all()
    recruiters = (
        await db.execute(
            select(Recruiter).where(Recruiter.company_id == company.id).order_by(Recruiter.name)
        )
    ).scalars().all()
    return {
        "note": note.note if note else "",
        "applications": [
            {
                "id": application.id,
                "job_id": job.id,
                "job_title": job.title,
                "status": application.status,
                "updated_at": application.updated_at,
            }
            for application, job in applications
        ],
        "recruiters": [
            {
                "id": recruiter.id,
                "name": recruiter.name,
                "email": recruiter.email,
                "linkedin_url": recruiter.linkedin_url,
                "title": recruiter.title,
            }
            for recruiter in recruiters
        ],
    }


@router.put("/{slug}/note")
async def save_company_note(
    slug: str, data: NoteBody, user: CurrentUser, db: DbSession
) -> dict[str, str]:
    company = await CompanyRepository(db).get_by_slug(slug)
    if company is None:
        raise HTTPException(404, detail="Company not found")
    result = await db.execute(
        select(ContactNote).where(
            ContactNote.user_id == user.id,
            ContactNote.company_id == company.id,
            ContactNote.recruiter_id.is_(None),
        )
    )
    row = result.scalar_one_or_none()
    if row:
        row.note = data.note
    else:
        db.add(ContactNote(user_id=user.id, company_id=company.id, note=data.note))
    await db.flush()
    return {"note": data.note}
