"""Jobs API endpoints."""

import hashlib
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.collectors.base import RawJob
from app.core.job_sources_catalog import sources_status_payload
from app.domain.country import country_filter_options
from app.models.job import Job
from app.models.job_preference import DismissedJob
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobDetail, JobSearchParams, PaginatedJobs
from app.services.ingestion_service import JobIngestionService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/countries")
async def list_job_countries(db: DbSession) -> dict:
    """Countries with active job counts for the filter dropdown."""
    rows = await JobRepository(db).list_countries()
    counts = {str(r["country"]): int(r["count"]) for r in rows if r.get("country")}
    options: list[dict[str, int | str]] = [{"country": "All countries", "count": sum(counts.values())}]
    for name in country_filter_options():
        count = counts.get(name, 0)
        if name == "Pakistan":
            count = sum(
                v for k, v in counts.items()
                if "pakistan" in k.lower()
                or any(c in k.lower() for c in ("lahore", "karachi", "islamabad", "rawalpindi"))
            )
        elif name == "India":
            count = 0
        elif count == 0:
            for key, val in counts.items():
                if name.lower() in key.lower() or key.lower() in name.lower():
                    count += val
        options.append({"country": name, "count": count})
    for country, count in counts.items():
        if country in ("India", "IN", "IND") or "india" in country.lower():
            continue
        if country not in {o["country"] for o in options}:
            options.append({"country": country, "count": count})
    return {"countries": options}


@router.get("/sources")
async def list_job_sources() -> dict:
    """Which job boards are connected and which need API keys."""
    return sources_status_payload()


@router.get("", response_model=PaginatedJobs)
async def list_jobs(
    db: DbSession,
    user: CurrentUser,
    q: str | None = None,
    work_mode: str | None = None,
    country: str | None = None,
    city: str | None = None,
    visa_sponsorship: bool | None = None,
    relocation: bool | None = None,
    experience_level: str | None = None,
    employment_type: str | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    company: str | None = None,
    source: str | None = None,
    added_today: bool | None = None,
    posted_within: str | None = None,
    sort_by: str = "posted_at",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedJobs:
    params = JobSearchParams(
        q=q,
        work_mode=work_mode,
        country=country,
        city=city,
        visa_sponsorship=visa_sponsorship,
        relocation=relocation,
        experience_level=experience_level,
        employment_type=employment_type,
        salary_min=salary_min,
        salary_max=salary_max,
        company=company,
        source=source,
        added_today=added_today,
        posted_within=posted_within,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return await JobRepository(db).search(params, user.id)


class DismissJobIn(BaseModel):
    reason: str | None = None


class FreelanceImportIn(BaseModel):
    url: str
    title: str | None = None
    description: str | None = None


@router.post("/import-freelance", response_model=JobDetail)
async def import_freelance_project(
    data: FreelanceImportIn, user: CurrentUser, db: DbSession
) -> JobDetail:
    parsed = urlparse(data.url.strip())
    host = parsed.netloc.lower().removeprefix("www.")
    platforms = {
        "upwork.com": "Upwork",
        "fiverr.com": "Fiverr",
        "freelancer.com": "Freelancer",
        "peopleperhour.com": "PeoplePerHour",
    }
    platform = next((name for domain, name in platforms.items() if host == domain or host.endswith(f".{domain}")), None)
    if not platform or parsed.scheme not in ("http", "https"):
        raise HTTPException(400, detail="Paste a valid Upwork, Fiverr, Freelancer, or PeoplePerHour link")

    title = (data.title or "").strip()
    description = (data.description or "").strip()
    if not title or not description:
        try:
            async with httpx.AsyncClient(
                timeout=12,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; JobHunter/1.0)"},
            ) as client:
                response = await client.get(data.url)
                response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            if not title:
                og_title = soup.select_one('meta[property="og:title"]')
                title = (og_title.get("content") if og_title else None) or (soup.title.string if soup.title else "")
            if not description:
                meta = soup.select_one('meta[property="og:description"], meta[name="description"]')
                description = (meta.get("content") if meta else "") or ""
        except Exception:
            pass
    title = title.strip().split("|")[0].strip() or f"{platform} software project"
    external_id = hashlib.sha256(data.url.strip().encode()).hexdigest()[:32]
    job = await JobIngestionService(db)._persist(
        RawJob(
            source=platform.lower(),
            external_id=external_id,
            title=title[:512],
            description=description[:10000] or "Imported freelance software/IT project.",
            company_name=platform,
            location_raw="Remote",
            work_mode="remote",
            employment_type="freelance",
            apply_url=data.url.strip(),
            source_url=data.url.strip(),
            posted_at=datetime.now(UTC),
        )
    )
    await db.commit()
    loaded = await JobRepository(db).get_by_id(job.id)
    return JobDetail.model_validate(loaded)


@router.post("/{job_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def dismiss_job(
    job_id: str, data: DismissJobIn, user: CurrentUser, db: DbSession
) -> Response:
    if await db.get(Job, job_id) is None:
        raise HTTPException(404, detail="Job not found")
    existing = await db.execute(
        select(DismissedJob).where(
            DismissedJob.user_id == user.id,
            DismissedJob.job_id == job_id,
        )
    )
    if existing.scalar_one_or_none() is None:
        db.add(DismissedJob(user_id=user.id, job_id=job_id, reason=data.reason))
        await db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: str, db: DbSession) -> JobDetail:
    job = await JobRepository(db).get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobDetail.model_validate(job)


@router.post("/refresh")
async def refresh_jobs(
    user: CurrentUser,
    db: DbSession,
    source: str | None = Query(None, description="Refresh one source only, e.g. linkedin"),
) -> dict:
    """Trigger a job refresh from all enabled connectors (or one source)."""
    service = JobIngestionService(db)
    if source:
        try:
            count = await service.refresh_by_source(source)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"status": "ok", "source": source, "count": count}
    stats = await service.refresh_all()
    return {"status": "ok", "sources": stats}
