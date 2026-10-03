"""Job repository with full-text search and filters."""

from datetime import UTC, datetime, timedelta
from math import ceil

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.datetime_utils import ensure_utc, posted_at_is_newer
from app.domain.location_filters import apply_exclude_india, is_india_job_filter
from app.models.company import Company
from app.models.job import Job
from app.models.job_preference import DismissedJob
from app.schemas.job import JobSearchParams, PaginatedJobs

PK_FILTER_CITIES = (
    "Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad",
    "Multan", "Peshawar", "Hyderabad", "Sialkot", "Gujranwala",
    "Quetta", "Bahawalpur", "Abbottabad",
)

PAKISTAN_SOURCES = ("pakistan", "indeed_pk", "rozee", "jooble_pk", "mustakbil")


class JobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _base_query(self) -> Select[tuple[Job]]:
        stmt = (
            select(Job)
            .options(selectinload(Job.company), selectinload(Job.recruiter))
            .where(Job.is_active.is_(True))
        )
        return apply_exclude_india(stmt)

    def _apply_filters(self, stmt: Select[tuple[Job]], params: JobSearchParams) -> Select[tuple[Job]]:
        if params.q:
            pattern = f"%{params.q}%"
            stmt = stmt.where(
                or_(
                    Job.title.ilike(pattern),
                    Job.description.ilike(pattern),
                    Job.requirements.ilike(pattern),
                    Job.technology_stack.ilike(pattern),
                    Job.location_raw.ilike(pattern),
                )
            )
        if params.work_mode:
            stmt = stmt.where(Job.work_mode == params.work_mode)
        if params.country:
            country = params.country.strip()
            if country.lower() in ("pakistan", "pk"):
                city_filters = [Job.city.ilike(f"%{c}%") for c in PK_FILTER_CITIES]
                stmt = stmt.where(
                    or_(
                        Job.country.ilike("%Pakistan%"),
                        Job.location_raw.ilike("%Pakistan%"),
                        Job.source.in_(PAKISTAN_SOURCES),
                        *city_filters,
                    )
                )
                stmt = stmt.where(
                    ~or_(
                        Job.location_raw.ilike("%india%"),
                        Job.location_raw.ilike("%telangana%"),
                        Job.location_raw.ilike("%maharashtra%"),
                    )
                )
            else:
                stmt = stmt.where(
                    or_(
                        Job.country.ilike(f"%{country}%"),
                        Job.location_raw.ilike(f"%{country}%"),
                        Job.city.ilike(f"%{country}%"),
                    )
                )
        if params.city:
            stmt = stmt.where(Job.city.ilike(f"%{params.city}%"))
        if params.visa_sponsorship is not None:
            stmt = stmt.where(Job.visa_sponsorship.is_(params.visa_sponsorship))
        if params.relocation is not None:
            stmt = stmt.where(Job.relocation.is_(params.relocation))
        if params.experience_level:
            stmt = stmt.where(Job.experience_level == params.experience_level)
        if params.employment_type:
            if params.employment_type == "freelance":
                stmt = stmt.where(
                    or_(
                        Job.employment_type == "freelance",
                        Job.source.in_(("freelance", "freelancer", "fiverr", "upwork", "peopleperhour")),
                    )
                )
            else:
                stmt = stmt.where(Job.employment_type == params.employment_type)
        if params.salary_min is not None:
            stmt = stmt.where(Job.salary_max >= params.salary_min)
        if params.salary_max is not None:
            stmt = stmt.where(Job.salary_min <= params.salary_max)
        if params.source:
            stmt = stmt.where(Job.source == params.source)
        if params.company:
            stmt = stmt.join(Company).where(Company.name.ilike(f"%{params.company}%"))
        if params.posted_within:
            now = datetime.now(UTC)
            if params.posted_within == "today":
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                stmt = stmt.where(Job.posted_at >= start)
            else:
                deltas = {
                    "week": timedelta(days=7),
                    "month": timedelta(days=30),
                }
                delta = deltas.get(params.posted_within)
                if delta:
                    stmt = stmt.where(Job.posted_at >= now - delta)
        if params.added_today:
            start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            stmt = stmt.where(Job.created_at >= start)
        return stmt

    def _apply_sort(self, stmt: Select[tuple[Job]], params: JobSearchParams) -> Select[tuple[Job]]:
        sort_map = {
            "posted_at": Job.posted_at,
            "created_at": Job.created_at,
            "salary_max": Job.salary_max,
            "title": Job.title,
            "match_score": Job.match_score,
            "recommendation_score": Job.recommendation_score,
        }
        column = sort_map.get(params.sort_by, Job.posted_at)
        if params.sort_order == "asc":
            return stmt.order_by(column.asc().nullslast(), Job.created_at.asc())
        return stmt.order_by(column.desc().nullslast(), Job.created_at.desc())

    async def search(self, params: JobSearchParams, user_id: str | None = None) -> PaginatedJobs:
        filtered = self._apply_filters(self._base_query(), params)
        if user_id:
            dismissed = select(DismissedJob.job_id).where(DismissedJob.user_id == user_id)
            filtered = filtered.where(Job.id.not_in(dismissed))
        count_stmt = select(func.count()).select_from(filtered.order_by(None).subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = self._apply_sort(filtered, params)
        offset = (params.page - 1) * params.page_size
        stmt = stmt.offset(offset).limit(params.page_size)
        result = await self.db.execute(stmt)
        items = list(result.scalars().unique().all())
        pages = ceil(total / params.page_size) if params.page_size and total > 0 else 0
        return PaginatedJobs(
            items=items,  # type: ignore[arg-type]
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )

    async def get_by_id(self, job_id: str) -> Job | None:
        stmt = (
            select(Job)
            .options(selectinload(Job.company), selectinload(Job.recruiter))
            .where(Job.id == job_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_hash(self, content_hash: str) -> Job | None:
        result = await self.db.execute(
            select(Job)
            .where(Job.content_hash == content_hash, Job.is_active.is_(True))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_source_external(self, source: str, external_id: str) -> Job | None:
        result = await self.db.execute(
            select(Job).where(Job.source == source, Job.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, job: Job) -> Job:
        existing = await self.get_by_source_external(job.source, job.external_id)
        if existing:
            for field in (
                "title",
                "description",
                "responsibilities",
                "requirements",
                "preferred_skills",
                "benefits",
                "technology_stack",
                "country",
                "city",
                "location_raw",
                "work_mode",
                "employment_type",
                "experience_level",
                "visa_sponsorship",
                "relocation",
                "salary_min",
                "salary_max",
                "salary_currency",
                "salary_period",
                "apply_url",
                "source_url",
                "posted_at",
                "expires_at",
                "is_active",
                "content_hash",
                "company_id",
            ):
                value = getattr(job, field)
                if value is None:
                    continue
                if field == "posted_at":
                    if posted_at_is_newer(value, existing.posted_at):
                        setattr(existing, field, ensure_utc(value))
                    continue
                setattr(existing, field, value)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        if job.posted_at is not None:
            job.posted_at = ensure_utc(job.posted_at)
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def list_countries(self) -> list[dict[str, int | str]]:
        stmt = (
            select(Job.country, func.count())
            .where(Job.is_active.is_(True), Job.country.is_not(None), Job.country != "")
            .where(~is_india_job_filter())
            .group_by(Job.country)
            .order_by(func.count().desc())
        )
        rows = (await self.db.execute(stmt)).all()
        return [{"country": row[0], "count": row[1]} for row in rows if row[0]]
