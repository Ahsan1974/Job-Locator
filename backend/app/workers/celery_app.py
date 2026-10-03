"""Celery application and scheduled tasks."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "java_career_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "refresh-jobs-hourly": {
            "task": "app.workers.tasks.refresh_jobs_task",
            "schedule": crontab(minute=15),
        },
        "expire-stale-jobs-daily": {
            "task": "app.workers.tasks.expire_stale_jobs_task",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)
