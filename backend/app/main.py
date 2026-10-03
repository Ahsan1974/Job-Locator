"""Java Career AI — FastAPI application entrypoint (local-first, no Docker)."""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, init_db
from app.services.default_user import ensure_default_user
from app.services.ingestion_service import refresh_all_jobs
from app.workers.scheduler import expire_jobs_job, start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


async def _startup_job_fetch() -> None:
    settings = get_settings()
    if not settings.refresh_jobs_on_startup:
        return
    try:
        stats = await refresh_all_jobs()
        logger.info("Startup job refresh: %s", stats)
    except Exception:
        logger.exception("Startup job refresh failed")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    await init_db()
    async with AsyncSessionLocal() as session:
        await ensure_default_user(session)
        await session.commit()
    start_scheduler()
    asyncio.create_task(expire_jobs_job())
    asyncio.create_task(_startup_job_fetch())
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description=(
            "AI-powered global Java career platform. "
            "Runs fully locally with SQLite — no Docker required. "
            "Phases 1–5: auth, jobs, resume match, recommendations, applications, analytics, AI tools."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=(
            None
            if settings.is_production
            else r"^https?://(?:localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|"
            r"10\.\d+\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)(?::\d+)?$"
        ),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix=settings.api_prefix)

    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    application.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name, "db": "sqlite" if settings.is_sqlite else "external"}

    return application


app = create_app()
