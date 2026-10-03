"""Celery background tasks."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from app.db.session import AsyncSessionLocal
from app.models.job import Job
from app.services.ingestion_service import JobIngestionService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(name="app.workers.tasks.refresh_jobs_task")
def refresh_jobs_task() -> dict:
    async def _inner() -> dict:
        async with AsyncSessionLocal() as session:
            stats = await JobIngestionService(session).refresh_all()
            return stats

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_inner())
        loop.close()
        logger.info("Job refresh complete: %s", result)
        return result
    except Exception:
        logger.exception("Job refresh failed")
        raise


@celery_app.task(name="app.workers.tasks.expire_stale_jobs_task")
def expire_stale_jobs_task(days: int = 60) -> int:
    async def _inner() -> int:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                update(Job)
                .where(Job.posted_at < cutoff, Job.is_active.is_(True))
                .values(is_active=False)
            )
            await session.commit()
            return result.rowcount or 0

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    count = loop.run_until_complete(_inner())
    loop.close()
    logger.info("Expired %s stale jobs", count)
    return count
