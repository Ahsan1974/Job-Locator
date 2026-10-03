"""Dashboard endpoints."""

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.job import ActivityItem, DashboardStats, JobListItem
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(user: CurrentUser, db: DbSession) -> DashboardStats:
    return await DashboardService(db).get_stats(user.id)


@router.get("/latest-jobs", response_model=list[JobListItem])
async def latest_jobs(
    user: CurrentUser,
    db: DbSession,
    limit: int = Query(10, ge=1, le=50),
) -> list[JobListItem]:
    return await DashboardService(db).latest_jobs(limit)


@router.get("/activity", response_model=list[ActivityItem])
async def recent_activity(
    user: CurrentUser,
    db: DbSession,
    limit: int = Query(15, ge=1, le=50),
) -> list[ActivityItem]:
    return await DashboardService(db).recent_activity(user.id, limit)
