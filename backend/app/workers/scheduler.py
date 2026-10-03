"""Local background scheduler — replaces Celery/Redis (no Docker)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.ingestion_service import JobIngestionService

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def refresh_jobs_job() -> None:
    logger.info("Scheduled job refresh starting")
    try:
        async with AsyncSessionLocal() as session:
            stats = await JobIngestionService(session).refresh_all()
            logger.info("Scheduled job refresh done: %s", stats)
    except Exception:
        logger.exception("Scheduled job refresh failed")


async def expire_jobs_job() -> None:
    from sqlalchemy import select, update

    from app.models.application import Application
    from app.models.job import Job
    from app.models.saved_job import SavedJob

    cutoff = datetime.now(UTC) - timedelta(days=45)
    async with AsyncSessionLocal() as session:
        protected_jobs = select(Application.job_id).union(select(SavedJob.job_id))
        await session.execute(
            update(Job)
            .where(
                Job.posted_at < cutoff,
                Job.is_active.is_(True),
                Job.id.not_in(protected_jobs),
            )
            .values(is_active=False)
        )
        await session.commit()


def start_scheduler() -> None:
    settings = get_settings()
    if not settings.enable_scheduler:
        return
    if scheduler.running:
        return
    minutes = max(15, settings.job_refresh_minutes)
    scheduler.add_job(refresh_jobs_job, "interval", minutes=minutes, id="refresh_jobs", replace_existing=True)
    scheduler.add_job(expire_jobs_job, "cron", hour=3, minute=0, id="expire_jobs", replace_existing=True)
    scheduler.start()
    logger.info("Local scheduler started (refresh every %s minutes)", minutes)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
