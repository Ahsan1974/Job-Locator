"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, companies, dashboard, jobs, saved_jobs
from app.api.v1.endpoints.intelligence import (
    ai_router,
    gap_router,
    match_router,
    rec_router,
    salary_router,
)
from app.api.v1.endpoints.resumes import router as resumes_router
from app.api.v1.endpoints.tracking import (
    alerts_router,
    analytics_router,
    apps_router,
    notif_router,
    recruiters_router,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(jobs.router)
api_router.include_router(dashboard.router)
api_router.include_router(companies.router)
api_router.include_router(saved_jobs.router)
api_router.include_router(resumes_router)
api_router.include_router(match_router)
api_router.include_router(rec_router)
api_router.include_router(salary_router)
api_router.include_router(gap_router)
api_router.include_router(ai_router)
api_router.include_router(apps_router)
api_router.include_router(alerts_router)
api_router.include_router(notif_router)
api_router.include_router(analytics_router)
api_router.include_router(recruiters_router)
