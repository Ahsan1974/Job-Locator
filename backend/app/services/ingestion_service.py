"""Connector registry and job ingestion service."""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.adzuna import AdzunaConnector
from app.collectors.arbeitnow import ArbeitnowConnector
from app.collectors.base import JobSourceConnector, RawJob
from app.collectors.careerjet import CareerjetConnector
from app.collectors.extra_boards import ExtraBoardsConnector
from app.collectors.findwork import FindworkConnector
from app.collectors.freelance_jobs import FreelanceJobsConnector
from app.collectors.greenhouse import GreenhouseConnector
from app.collectors.himalayas import HimalayasConnector
from app.collectors.hn_algolia import HnAlgoliaConnector
from app.collectors.jobicy import JobicyConnector
from app.collectors.jooble import JoobleConnector
from app.collectors.jsearch import JSearchConnector
from app.collectors.lever import LeverConnector
from app.collectors.linkedin_jobs import LinkedInJobsConnector
from app.collectors.pakistan_jobs import PakistanJobsConnector
from app.collectors.regional_jobs import RegionalJobsConnector
from app.collectors.remoteok import RemoteOKConnector
from app.collectors.remotive import RemotiveConnector
from app.collectors.rss_feeds import RssFeedsConnector
from app.collectors.usajobs import USAJobsConnector
from app.collectors.weworkremotely import WeWorkRemotelyConnector
from app.collectors.working_nomads import WorkingNomadsConnector
from app.core.config import get_settings
from app.domain.country import normalize_country
from app.domain.datetime_utils import ensure_utc
from app.domain.job_dedupe import collapse_duplicate_jobs, job_fingerprint
from app.models.job import Job
from app.repositories.company_repository import CompanyRepository
from app.repositories.job_repository import JobRepository
from app.services.notification_service import notify_new_job

logger = logging.getLogger(__name__)


def get_connectors() -> list[JobSourceConnector]:
    settings = get_settings()
    connectors: list[JobSourceConnector] = [
        RegionalJobsConnector(),
        PakistanJobsConnector(),
        JoobleConnector(),
        JSearchConnector(),
        CareerjetConnector(),
        GreenhouseConnector(),
        LeverConnector(),
        HnAlgoliaConnector(),
        AdzunaConnector(),
        RemoteOKConnector(),
        RemotiveConnector(),
        ArbeitnowConnector(),
        JobicyConnector(),
        HimalayasConnector(),
        WorkingNomadsConnector(),
        RssFeedsConnector(),
        WeWorkRemotelyConnector(),
        FindworkConnector(),
        ExtraBoardsConnector(),
        FreelanceJobsConnector(),
        USAJobsConnector(),
    ]
    if settings.enable_linkedin_scraping:
        connectors.insert(1, LinkedInJobsConnector())
    return connectors


async def refresh_all_jobs(limit_per_source: int | None = None) -> dict[str, int]:
    """Standalone refresh for startup / scheduler (creates its own session)."""
    from app.db.session import AsyncSessionLocal

    settings = get_settings()
    limit = limit_per_source or settings.job_fetch_limit_per_source
    async with AsyncSessionLocal() as session:
        service = JobIngestionService(session)
        stats = await service.refresh_all(limit_per_source=limit)
        await _deactivate_placeholders(session)
        return stats


async def _deactivate_placeholders(session: AsyncSession) -> None:
    """Hide demo/placeholder jobs and fix misclassified listings."""
    from sqlalchemy import or_, update

    from app.models.job import Job

    await session.execute(update(Job).where(Job.source == "seed").values(is_active=False))
    await session.execute(
        update(Job).where(Job.apply_url.like("%example.com%")).values(is_active=False)
    )
    await session.execute(
        update(Job)
        .where(
            Job.country.ilike("%Pakistan%"),
            or_(
                Job.location_raw.ilike("%india%"),
                Job.location_raw.ilike("%telangana%"),
                Job.location_raw.ilike("%maharashtra%"),
                Job.location_raw.ilike("%bengaluru%"),
                Job.location_raw.ilike("%bangalore%"),
            ),
        )
        .values(is_active=False)
    )
    await session.execute(
        update(Job)
        .where(
            or_(
                Job.country.in_(("India", "IN", "IND")),
                Job.country.ilike("%India%"),
                Job.location_raw.ilike("%india%"),
            )
        )
        .values(is_active=False)
    )
    await session.commit()
    await collapse_duplicate_jobs(session)


class JobIngestionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.jobs = JobRepository(db)
        self.companies = CompanyRepository(db)

    def _limit_for(self, name: str, limit_per_source: int) -> int:
        settings = get_settings()
        if name == "linkedin":
            return settings.linkedin_fetch_limit
        if name == "pakistan":
            return settings.pakistan_fetch_limit
        if name == "freelance":
            return 60
        return limit_per_source

    async def refresh_all(self, limit_per_source: int = 50) -> dict[str, int]:
        connectors = get_connectors()

        async def _fetch(connector: JobSourceConnector) -> tuple[str, list]:
            limit = self._limit_for(connector.name, limit_per_source)
            raw_jobs = await connector.fetch(limit=limit)
            return connector.name, raw_jobs

        fetched = await asyncio.gather(*[_fetch(c) for c in connectors], return_exceptions=True)
        stats: dict[str, int] = {}
        for connector, result in zip(connectors, fetched):
            if isinstance(result, Exception):
                logger.warning("Failed to fetch source %s: %s", connector.name, result)
                stats[connector.name] = -1
                continue
            _name, raw_jobs = result
            try:
                saved = 0
                for raw in raw_jobs:
                    try:
                        async with self.db.begin_nested():
                            await self._persist(raw)
                        saved += 1
                    except Exception as exc:
                        logger.warning("Skip job from %s (%s): %s", connector.name, raw.external_id, exc)
                await self.db.commit()
                stats[connector.name] = saved
            except Exception as exc:
                logger.warning("Failed to save source %s: %s", connector.name, exc)
                await self.db.rollback()
                stats[connector.name] = -1
        await _deactivate_placeholders(self.db)
        return stats

    async def refresh_by_source(self, source: str, limit: int | None = None) -> int:
        settings = get_settings()
        for connector in get_connectors():
            if connector.name == source:
                job_limit = limit or (
                    settings.linkedin_fetch_limit if source == "linkedin" else settings.job_fetch_limit_per_source
                )
                count = await self.refresh_source(connector, limit=job_limit)
                await _deactivate_placeholders(self.db)
                return count
        raise ValueError(f"Unknown job source: {source}")

    async def refresh_source(self, connector: JobSourceConnector, limit: int = 50) -> int:
        raw_jobs = await connector.fetch(limit=limit)
        saved = 0
        for raw in raw_jobs:
            try:
                async with self.db.begin_nested():
                    await self._persist(raw)
                saved += 1
            except Exception as exc:
                logger.warning(
                    "Skip job from %s (%s): %s",
                    connector.name,
                    raw.external_id,
                    exc,
                )
        await self.db.commit()
        return saved

    async def _persist(self, raw: RawJob) -> Job:
        existing_source_job = await self.jobs.get_by_source_external(raw.source, raw.external_id)
        company_id = None
        if raw.company_name:
            company = await self.companies.get_or_create(
                raw.company_name,
                website=raw.company_website,
                logo_url=raw.company_logo,
                country=raw.country,
            )
            company_id = company.id

        content_hash = job_fingerprint(
            raw.title,
            raw.company_name,
            raw.location_raw or raw.city or raw.country,
            raw.apply_url,
        )
        duplicate = await self.jobs.get_active_by_hash(content_hash)
        if duplicate and not (
            duplicate.source == raw.source and duplicate.external_id == raw.external_id
        ):
            return duplicate

        job = Job(
            company_id=company_id,
            title=raw.title,
            description=raw.description,
            requirements=raw.requirements,
            benefits=raw.benefits,
            technology_stack=json.dumps(raw.technology_stack) if raw.technology_stack else None,
            country=normalize_country(raw.country),
            city=raw.city,
            location_raw=raw.location_raw,
            work_mode=raw.work_mode,
            employment_type=raw.employment_type,
            experience_level=raw.experience_level,
            visa_sponsorship=raw.visa_sponsorship,
            relocation=raw.relocation,
            salary_min=raw.salary_min,
            salary_max=raw.salary_max,
            salary_currency=raw.salary_currency,
            salary_period=raw.salary_period,
            source=raw.source,
            external_id=raw.external_id,
            apply_url=raw.apply_url or raw.source_url,
            source_url=raw.source_url or raw.apply_url,
            posted_at=ensure_utc(raw.posted_at) if raw.posted_at else None,
            content_hash=content_hash,
            is_active=True,
        )
        saved = await self.jobs.upsert(job)
        posted_at = ensure_utc(saved.posted_at) if saved.posted_at else None
        is_recent = posted_at is None or posted_at >= datetime.now(UTC) - timedelta(days=7)
        if existing_source_job is None and is_recent:
            await notify_new_job(self.db, saved, raw.company_name)
        return saved
