"""Dashboard statistics service."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.company import Company
from app.models.job import Job
from app.models.saved_job import SavedJob
from app.schemas.job import ActivityItem, DashboardStats, JobListItem


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_stats(self, user_id: str) -> DashboardStats:
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        total_jobs = await self._scalar(select(func.count()).select_from(Job).where(Job.is_active.is_(True)))
        jobs_today = await self._scalar(
            select(func.count())
            .select_from(Job)
            .where(Job.created_at >= today_start, Job.is_active.is_(True))
        )
        remote_jobs = await self._scalar(
            select(func.count())
            .select_from(Job)
            .where(Job.work_mode == "remote", Job.is_active.is_(True))
        )
        visa_jobs = await self._scalar(
            select(func.count())
            .select_from(Job)
            .where(Job.visa_sponsorship.is_(True), Job.is_active.is_(True))
        )
        avg_salary = await self._scalar(
            select(func.avg((Job.salary_min + Job.salary_max) / 2)).where(
                Job.salary_min.is_not(None),
                Job.salary_max.is_not(None),
                Job.is_active.is_(True),
            )
        )
        countries = await self._scalar(
            select(func.count(distinct(Job.country))).where(
                Job.country.is_not(None), Job.is_active.is_(True)
            )
        )
        companies = await self._scalar(
            select(func.count()).select_from(Company)
        )
        saved = await self._scalar(
            select(func.count()).select_from(SavedJob).where(SavedJob.user_id == user_id)
        )
        applications = await self._scalar(
            select(func.count()).select_from(Application).where(Application.user_id == user_id)
        )
        recommended = await self._scalar(
            select(func.count())
            .select_from(Job)
            .where(
                Job.recommendation_priority == "high",
                Job.is_active.is_(True),
            )
        )

        return DashboardStats(
            total_jobs=total_jobs or 0,
            jobs_added_today=jobs_today or 0,
            remote_jobs=remote_jobs or 0,
            visa_sponsorship_jobs=visa_jobs or 0,
            average_salary=float(avg_salary) if avg_salary else None,
            countries_count=countries or 0,
            companies_hiring=companies or 0,
            saved_jobs=saved or 0,
            applications=applications or 0,
            recommended_jobs=recommended or 0,
        )

    async def latest_jobs(self, limit: int = 10) -> list[JobListItem]:
        from sqlalchemy.orm import selectinload

        result = await self.db.execute(
            select(Job)
            .options(selectinload(Job.company))
            .where(Job.is_active.is_(True))
            .order_by(Job.posted_at.desc().nullslast())
            .limit(limit)
        )
        jobs = result.scalars().all()
        return [JobListItem.model_validate(j) for j in jobs]

    async def recent_activity(self, user_id: str, limit: int = 15) -> list[ActivityItem]:
        items: list[ActivityItem] = []

        saved = await self.db.execute(
            select(SavedJob)
            .where(SavedJob.user_id == user_id)
            .order_by(SavedJob.created_at.desc())
            .limit(limit)
        )
        for row in saved.scalars().all():
            items.append(
                ActivityItem(
                    id=row.id,
                    type="saved",
                    title="Saved a job",
                    subtitle=row.job_id,
                    timestamp=row.created_at,
                    link=f"/jobs/{row.job_id}",
                )
            )

        apps = await self.db.execute(
            select(Application)
            .where(Application.user_id == user_id)
            .order_by(Application.updated_at.desc())
            .limit(limit)
        )
        for row in apps.scalars().all():
            items.append(
                ActivityItem(
                    id=row.id,
                    type="application",
                    title=f"Application: {row.status}",
                    subtitle=row.job_id,
                    timestamp=row.updated_at,
                    link=f"/applications/{row.id}",
                )
            )

        def _stamp(value):
            if value is None:
                return datetime.min.replace(tzinfo=UTC)
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value.astimezone(UTC)

        items.sort(key=lambda x: _stamp(x.timestamp), reverse=True)
        return items[:limit]

    async def _scalar(self, stmt) -> int | float | None:
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
