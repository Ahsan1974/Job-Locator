"""Create dashboard notifications and optionally deliver standards-based Web Push."""

import asyncio
import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.job import Job
from app.models.job_preference import PushSubscription
from app.models.notification import Notification
from app.models.user import User

logger = logging.getLogger(__name__)


async def notify_new_job(db: AsyncSession, job: Job, company_name: str | None) -> None:
    """Notify active users about a genuinely new listing."""
    users = (
        await db.execute(select(User).where(User.is_active.is_(True)))
    ).scalars().all()
    if not users:
        return

    company = company_name or "A company"
    title = f"{company} is hiring"
    body = job.title
    link = f"/jobs/{job.id}"
    for user in users:
        db.add(
            Notification(
                user_id=user.id,
                title=title,
                body=body,
                notification_type="new_job",
                link=link,
                channel="push",
            )
        )
    await db.flush()

    settings = get_settings()
    if not settings.vapid_private_key or not settings.vapid_public_key:
        return
    subscriptions = (
        await db.execute(
            select(PushSubscription).where(
                PushSubscription.user_id.in_([user.id for user in users])
            )
        )
    ).scalars().all()
    if not subscriptions:
        return

    payload = json.dumps({"title": title, "body": body, "url": link, "jobId": job.id})
    await asyncio.gather(
        *[_send_web_push(subscription, payload) for subscription in subscriptions],
        return_exceptions=True,
    )


async def _send_web_push(subscription: PushSubscription, payload: str) -> None:
    settings = get_settings()

    def send() -> None:
        from pywebpush import WebPushException, webpush

        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject},
            )
        except WebPushException as exc:
            logger.warning("Web push delivery failed: %s", exc)

    await asyncio.to_thread(send)
