"""Applications, alerts, notifications, analytics, recruiters."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.constants import ApplicationStatus
from app.domain.skills import extract_skills, parse_json_list
from app.models.application import Application
from app.models.contact_note import ContactNote
from app.models.job import Job
from app.models.job_preference import PushSubscription
from app.models.notification import Alert, Notification
from app.models.recruiter import Recruiter
from app.schemas.job import JobListItem

apps_router = APIRouter(prefix="/applications", tags=["Applications"])
alerts_router = APIRouter(prefix="/alerts", tags=["Alerts"])
notif_router = APIRouter(prefix="/notifications", tags=["Notifications"])
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])
recruiters_router = APIRouter(prefix="/recruiters", tags=["Recruiters"])


class ApplicationCreate(BaseModel):
    job_id: str
    status: str | None = ApplicationStatus.APPLIED.value
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    reminder_date: str | None = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    job: JobListItem | None = None
    status: str
    notes: str | None = None
    applied_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


@apps_router.get("", response_model=list[ApplicationOut])
async def list_applications(user: CurrentUser, db: DbSession) -> list[ApplicationOut]:
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job).selectinload(Job.company))
        .where(Application.user_id == user.id)
        .order_by(Application.updated_at.desc())
    )
    rows = result.scalars().all()
    out: list[ApplicationOut] = []
    for row in rows:
        item = ApplicationOut(
            id=row.id,
            job_id=row.job_id,
            status=row.status,
            notes=row.notes,
            applied_at=row.applied_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
            job=JobListItem.model_validate(row.job) if row.job else None,
        )
        out.append(item)
    return out


@apps_router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate, user: CurrentUser, db: DbSession
) -> ApplicationOut:
    job = await db.get(Job, data.job_id)
    if job is None:
        raise HTTPException(404, detail="Job not found")
    existing = await db.execute(
        select(Application).where(
            Application.user_id == user.id, Application.job_id == data.job_id
        )
    )
    row = existing.scalar_one_or_none()
    if row:
        row.status = data.status or row.status
        if data.notes is not None:
            row.notes = data.notes
    else:
        row = Application(
            user_id=user.id,
            job_id=data.job_id,
            status=data.status or ApplicationStatus.APPLIED.value,
            notes=data.notes,
            applied_at=datetime.now(UTC),
            history=json.dumps([{"status": data.status or "applied", "at": datetime.now(UTC).isoformat()}]),
        )
        db.add(row)
    await db.flush()
    await db.refresh(row)
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job).selectinload(Job.company))
        .where(Application.id == row.id)
    )
    row = result.scalar_one()
    return ApplicationOut(
        id=row.id,
        job_id=row.job_id,
        status=row.status,
        notes=row.notes,
        applied_at=row.applied_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
        job=JobListItem.model_validate(row.job) if row.job else None,
    )


@apps_router.patch("/{app_id}", response_model=ApplicationOut)
async def update_application(
    app_id: str, data: ApplicationUpdate, user: CurrentUser, db: DbSession
) -> ApplicationOut:
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job).selectinload(Job.company))
        .where(Application.id == app_id, Application.user_id == user.id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, detail="Application not found")
    if data.status is not None:
        row.status = data.status
    if data.notes is not None:
        row.notes = data.notes
    await db.flush()
    await db.refresh(row)
    return ApplicationOut(
        id=row.id,
        job_id=row.job_id,
        status=row.status,
        notes=row.notes,
        applied_at=row.applied_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
        job=JobListItem.model_validate(row.job) if row.job else None,
    )


@apps_router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_application(app_id: str, user: CurrentUser, db: DbSession) -> Response:
    result = await db.execute(
        select(Application).where(Application.id == app_id, Application.user_id == user.id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, detail="Application not found")
    await db.delete(row)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Alerts ────────────────────────────────────────────────────────────────────


class AlertIn(BaseModel):
    name: str | None = None
    keywords: list[str] | None = None
    countries: list[str] | None = None
    work_modes: list[str] | None = None
    min_salary: int | None = None
    channels: list[str] | None = None
    is_active: bool | None = None


class AlertCreate(BaseModel):
    name: str
    keywords: list[str] = []
    countries: list[str] = []
    work_modes: list[str] = []
    min_salary: int | None = None
    channels: list[str] = ["dashboard"]
    is_active: bool = True


class AlertOut(BaseModel):
    id: str
    name: str
    keywords: list[str]
    countries: list[str]
    work_modes: list[str]
    min_salary: int | None
    channels: list[str]
    is_active: bool
    created_at: datetime


def _alert_out(a: Alert) -> AlertOut:
    filters = {}
    if a.filters_json:
        try:
            filters = json.loads(a.filters_json)
        except json.JSONDecodeError:
            filters = {}
    return AlertOut(
        id=a.id,
        name=a.name,
        keywords=filters.get("keywords") or ([a.query] if a.query else []),
        countries=filters.get("countries") or [],
        work_modes=filters.get("work_modes") or [],
        min_salary=filters.get("min_salary"),
        channels=parse_json_list(a.channels) or ["dashboard"],
        is_active=a.is_active,
        created_at=a.created_at,
    )


@alerts_router.get("", response_model=list[AlertOut])
async def list_alerts(user: CurrentUser, db: DbSession) -> list[AlertOut]:
    result = await db.execute(
        select(Alert).where(Alert.user_id == user.id).order_by(Alert.created_at.desc())
    )
    return [_alert_out(a) for a in result.scalars().all()]


@alerts_router.post("", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
async def create_alert(data: AlertCreate, user: CurrentUser, db: DbSession) -> AlertOut:
    filters = {
        "keywords": data.keywords,
        "countries": data.countries,
        "work_modes": data.work_modes,
        "min_salary": data.min_salary,
    }
    row = Alert(
        user_id=user.id,
        name=data.name,
        query=", ".join(data.keywords) if data.keywords else None,
        filters_json=json.dumps(filters),
        channels=json.dumps(data.channels),
        is_active=data.is_active,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return _alert_out(row)


@alerts_router.patch("/{alert_id}", response_model=AlertOut)
async def update_alert(alert_id: str, data: AlertIn, user: CurrentUser, db: DbSession) -> AlertOut:
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == user.id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, detail="Alert not found")
    payload = data.model_dump(exclude_unset=True)
    if "name" in payload and data.name is not None:
        row.name = data.name
    filters = {}
    if row.filters_json:
        try:
            filters = json.loads(row.filters_json)
        except json.JSONDecodeError:
            filters = {}
    for key in ("keywords", "countries", "work_modes", "min_salary"):
        if key in payload:
            filters[key] = payload[key]
    if any(k in payload for k in ("keywords", "countries", "work_modes", "min_salary")):
        row.filters_json = json.dumps(filters)
        if data.keywords is not None:
            row.query = ", ".join(data.keywords)
    if "channels" in payload and data.channels is not None:
        row.channels = json.dumps(data.channels)
    if data.is_active is not None:
        row.is_active = data.is_active
    await db.flush()
    await db.refresh(row)
    return _alert_out(row)


@alerts_router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_alert(alert_id: str, user: CurrentUser, db: DbSession) -> Response:
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == user.id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, detail="Alert not found")
    await db.delete(row)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Notifications ─────────────────────────────────────────────────────────────


class NotificationOut(BaseModel):
    id: str
    title: str
    message: str | None
    type: str
    is_read: bool
    link: str | None
    created_at: datetime


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionIn(BaseModel):
    endpoint: str
    keys: PushKeys


@notif_router.get("", response_model=list[NotificationOut])
async def list_notifications(user: CurrentUser, db: DbSession) -> list[NotificationOut]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    return [
        NotificationOut(
            id=n.id,
            title=n.title,
            message=n.body,
            type=getattr(n, "notification_type", None) or "info",
            is_read=n.is_read,
            link=n.link,
            created_at=n.created_at,
        )
        for n in result.scalars().all()
    ]


@notif_router.post("/{notif_id}/read")
async def mark_read(notif_id: str, user: CurrentUser, db: DbSession) -> dict:
    result = await db.execute(
        select(Notification).where(Notification.id == notif_id, Notification.user_id == user.id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, detail="Notification not found")
    row.is_read = True
    await db.flush()
    return {"ok": True}


@notif_router.post("/read-all")
async def mark_all_read(user: CurrentUser, db: DbSession) -> dict:
    result = await db.execute(
        select(Notification).where(Notification.user_id == user.id, Notification.is_read.is_(False))
    )
    for n in result.scalars().all():
        n.is_read = True
    await db.flush()
    return {"ok": True}


@notif_router.get("/push/config")
async def push_config() -> dict[str, str | bool]:
    public_key = get_settings().vapid_public_key
    return {"enabled": bool(public_key), "public_key": public_key}


@notif_router.post("/push/subscribe")
async def subscribe_push(
    data: PushSubscriptionIn, request: Request, user: CurrentUser, db: DbSession
) -> dict[str, bool]:
    result = await db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == data.endpoint)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = PushSubscription(
            user_id=user.id,
            endpoint=data.endpoint,
            p256dh=data.keys.p256dh,
            auth=data.keys.auth,
            user_agent=request.headers.get("user-agent"),
        )
        db.add(row)
    else:
        row.user_id = user.id
        row.p256dh = data.keys.p256dh
        row.auth = data.keys.auth
    await db.flush()
    return {"ok": True}


@notif_router.delete("/push/subscribe")
async def unsubscribe_push(endpoint: str, user: CurrentUser, db: DbSession) -> dict[str, bool]:
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == user.id,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
    return {"ok": True}


# ── Analytics ─────────────────────────────────────────────────────────────────


@analytics_router.get("/overview")
async def analytics_overview(user: CurrentUser, db: DbSession) -> dict:
    apps = (
        await db.execute(select(Application).where(Application.user_id == user.id))
    ).scalars().all()
    jobs = (
        await db.execute(select(Job).where(Job.is_active.is_(True)).limit(500))
    ).scalars().all()

    by_day: dict[str, int] = defaultdict(int)
    for a in apps:
        day = (a.applied_at or a.created_at).date().isoformat()
        by_day[day] += 1
    # fill last 14 days
    applications_over_time = []
    for i in range(13, -1, -1):
        d = (datetime.now(UTC) - timedelta(days=i)).date().isoformat()
        applications_over_time.append({"date": d, "count": by_day.get(d, 0)})

    country_counts = Counter(j.country or "Unknown" for j in jobs)
    jobs_by_country = [{"country": k, "count": v} for k, v in country_counts.most_common(10)]

    tech_counter: Counter[str] = Counter()
    for j in jobs:
        for t in extract_skills(f"{j.title} {j.technology_stack or ''} {j.description or ''}")[:8]:
            tech_counter[t] += 1
    tech_demand = [{"technology": k, "count": v} for k, v in tech_counter.most_common(12)]

    buckets = {"0-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
    for j in jobs:
        s = float(j.match_score or j.recommendation_score or 0)
        if s < 40:
            buckets["0-40"] += 1
        elif s < 60:
            buckets["40-60"] += 1
        elif s < 80:
            buckets["60-80"] += 1
        else:
            buckets["80-100"] += 1
    match_distribution = [{"range": k, "count": v} for k, v in buckets.items()]

    status_counts = Counter(a.status for a in apps)
    status_breakdown = [{"status": k, "count": v} for k, v in status_counts.items()]

    return {
        "applications_over_time": applications_over_time,
        "jobs_by_country": jobs_by_country,
        "tech_demand": tech_demand,
        "match_distribution": match_distribution,
        "status_breakdown": status_breakdown,
    }


# ── Recruiters ────────────────────────────────────────────────────────────────


@recruiters_router.get("")
async def list_recruiters(user: CurrentUser, db: DbSession) -> list[dict]:
    result = await db.execute(
        select(Recruiter).options(selectinload(Recruiter.company)).order_by(Recruiter.name).limit(100)
    )
    out = []
    for r in result.scalars().all():
        note = (
            await db.execute(
                select(ContactNote).where(
                    ContactNote.user_id == user.id,
                    ContactNote.recruiter_id == r.id,
                )
            )
        ).scalar_one_or_none()
        company = None
        if r.company:
            company = {
                "id": r.company.id,
                "name": r.company.name,
                "slug": r.company.slug,
                "logo_url": r.company.logo_url,
                "website": r.company.website,
                "industry": r.company.industry,
                "company_size": r.company.company_size,
                "offers_visa_sponsorship": r.company.offers_visa_sponsorship,
            }
        out.append(
            {
                "id": r.id,
                "name": r.name,
                "company": company,
                "email": r.email,
                "linkedin_url": r.linkedin_url,
                "specialization": r.title,
                "note": note.note if note else "",
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
        )
    return out


class RecruiterNoteBody(BaseModel):
    note: str


@recruiters_router.put("/{recruiter_id}/note")
async def save_recruiter_note(
    recruiter_id: str, data: RecruiterNoteBody, user: CurrentUser, db: DbSession
) -> dict[str, str]:
    recruiter = await db.get(Recruiter, recruiter_id)
    if recruiter is None:
        raise HTTPException(404, detail="Recruiter not found")
    result = await db.execute(
        select(ContactNote).where(
            ContactNote.user_id == user.id,
            ContactNote.recruiter_id == recruiter_id,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        row.note = data.note
    else:
        db.add(
            ContactNote(
                user_id=user.id,
                company_id=recruiter.company_id,
                recruiter_id=recruiter.id,
                note=data.note,
            )
        )
    await db.flush()
    return {"note": data.note}
