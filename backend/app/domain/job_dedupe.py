"""Cross-source duplicate detection for job listings."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.job import Job


def _norm(value: str | None) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", (value or "").lower())
    return " ".join(text.split())


def _title_key(value: str) -> str:
    text = value.lower()
    text = re.sub(r"\((?:m/?f/?d|remote|hybrid|onsite)\)", " ", text)
    text = re.sub(r"\[(?:remote|hybrid|onsite)\]", " ", text)
    text = re.sub(r"\s[-|]\s(?:remote|hybrid|onsite|[a-z .]+,\s*[a-z]{2})$", " ", text)
    return _norm(text)


def _company_key(value: str | None) -> str:
    text = _norm(value)
    return re.sub(r"\b(?:inc|llc|ltd|limited|gmbh|corp|corporation|co)\b", "", text).strip()


def job_fingerprint(
    title: str,
    company: str | None,
    location: str | None = None,
    apply_url: str | None = None,
) -> str:
    """Same role at the same company collapses across boards."""
    title_key = _title_key(title)
    company_key = _company_key(company)
    if company_key:
        raw = f"{title_key}|{company_key}"
    else:
        raw = f"{title_key}|{_norm(apply_url) or _norm(location)}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _posted_key(job: Job) -> datetime:
    posted = job.posted_at
    if posted is None:
        return datetime.min.replace(tzinfo=UTC)
    if posted.tzinfo is None:
        return posted.replace(tzinfo=UTC)
    return posted.astimezone(UTC)


async def collapse_duplicate_jobs(session: AsyncSession) -> int:
    """Keep the newest copy of each title+company and hide the rest."""
    result = await session.execute(
        select(Job).options(selectinload(Job.company)).where(Job.is_active.is_(True))
    )
    jobs = list(result.scalars().unique().all())
    groups: dict[str, list[Job]] = {}
    for job in jobs:
        company = job.company.name if job.company else None
        fingerprint = job_fingerprint(
            job.title,
            company,
            job.location_raw or job.city or job.country,
            job.apply_url,
        )
        job.content_hash = fingerprint
        groups.setdefault(fingerprint, []).append(job)

    hidden = 0
    for group in groups.values():
        if len(group) < 2:
            continue
        group.sort(key=_posted_key, reverse=True)
        for extra in group[1:]:
            extra.is_active = False
            hidden += 1
    await session.commit()
    return hidden
