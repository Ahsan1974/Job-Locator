"""Match, live-view, recommendations, salary, skill-gap, AI endpoints."""

from __future__ import annotations

import json
from math import ceil

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.domain.skills import extract_skills, parse_json_list
from app.models.job import Job
from app.models.resume import Resume
from app.schemas.job import JobDetail, JobListItem
from app.services.ai_service import AIContentService
from app.services.match_engine import ResumeMatchEngine
from app.services.pdf_service import build_application_pack_pdf, build_resume_pdf
from app.services.recommendation_engine import RecommendationEngine
from app.services.salary_estimator import SalaryEstimator
from app.services.skill_gap_engine import SkillGapEngine

match_router = APIRouter(tags=["Match"])
rec_router = APIRouter(prefix="/recommendations", tags=["Recommendations"])
salary_router = APIRouter(prefix="/salary", tags=["Salary"])
gap_router = APIRouter(prefix="/skill-gap", tags=["Skill Gap"])
ai_router = APIRouter(prefix="/ai", tags=["AI"])


async def _primary_resume(db, user_id: str) -> Resume | None:
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == user_id, Resume.is_primary.is_(True))
        .limit(1)
    )
    resume = result.scalar_one_or_none()
    if resume:
        return resume
    result = await db.execute(
        select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


def _job_blob(job: Job) -> str:
    parts = [
        job.title or "",
        job.description or "",
        job.requirements or "",
        job.preferred_skills or "",
        job.technology_stack or "",
    ]
    return "\n".join(parts)


@match_router.get("/match/job/{job_id}")
async def match_job(job_id: str, user: CurrentUser, db: DbSession) -> dict:
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, detail="Job not found")
    resume = await _primary_resume(db, user.id)
    if resume is None or not resume.raw_text:
        raise HTTPException(400, detail="Upload a resume first")
    skills = parse_json_list(resume.skills)
    result = ResumeMatchEngine().score(resume.raw_text, _job_blob(job), skills)
    job.match_score = result["overall"]
    await db.flush()
    return result


@match_router.get("/jobs/{job_id}/live-view")
async def live_view(job_id: str, user: CurrentUser, db: DbSession) -> dict:
    result = await db.execute(
        select(Job).options(selectinload(Job.company)).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(404, detail="Job not found")
    resume = await _primary_resume(db, user.id)
    match = {"matching_skills": [], "missing_skills": [], "missing_keywords": []}
    resume_out = None
    if resume and resume.raw_text:
        match = ResumeMatchEngine().score(
            resume.raw_text, _job_blob(job), parse_json_list(resume.skills)
        )
        resume_out = {
            "id": resume.id,
            "filename": resume.filename,
            "file_url": None,
            "is_primary": resume.is_primary,
            "parsed_skills": parse_json_list(resume.skills),
            "parsed_experience": str(resume.experience_years) if resume.experience_years else None,
            "parsed_education": resume.education,
            "raw_text": resume.raw_text,
            "created_at": resume.created_at.isoformat() if resume.created_at else "",
            "updated_at": resume.updated_at.isoformat() if resume.updated_at else "",
        }
    return {
        "job": JobDetail.model_validate(job).model_dump(mode="json"),
        "resume": resume_out,
        "matching_skills": match.get("matching_skills", []),
        "missing_skills": match.get("missing_skills", []),
        "matching_keywords": match.get("matching_skills", []),
    }


@rec_router.get("")
async def list_recommendations(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    priority: str | None = None,
) -> dict:
    stmt = (
        select(Job)
        .options(selectinload(Job.company))
        .where(Job.is_active.is_(True), Job.recommendation_score.is_not(None))
        .order_by(Job.recommendation_score.desc())
    )
    if priority:
        stmt = stmt.where(Job.recommendation_priority == priority)
    result = await db.execute(stmt)
    jobs = list(result.scalars().unique().all())
    total = len(jobs)
    start = (page - 1) * page_size
    page_items = jobs[start : start + page_size]
    return {
        "items": [JobListItem.model_validate(j) for j in page_items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": ceil(total / page_size) if page_size else 0,
    }


@rec_router.post("/recompute")
async def recompute_recommendations(user: CurrentUser, db: DbSession) -> dict:
    resume = await _primary_resume(db, user.id)
    if resume is None or not resume.raw_text:
        raise HTTPException(400, detail="Upload a primary resume first")
    skills = parse_json_list(resume.skills)
    preferred_modes = parse_json_list(user.preferred_work_modes) if user.preferred_work_modes else []
    engine = RecommendationEngine()
    result = await db.execute(select(Job).where(Job.is_active.is_(True)))
    jobs = result.scalars().all()
    updated = 0
    for job in jobs:
        score, priority = engine.score_job(
            resume_text=resume.raw_text,
            resume_skills=skills,
            job_text=_job_blob(job),
            work_mode=job.work_mode,
            visa=job.visa_sponsorship,
            preferred_modes=preferred_modes,
            visa_required=user.visa_sponsorship_required,
            salary_min=float(job.salary_min) if job.salary_min is not None else None,
            salary_expectation=user.salary_expectation_min,
        )
        job.recommendation_score = score
        job.recommendation_priority = priority
        job.match_score = score
        updated += 1
    await db.flush()
    return {"updated": updated}


class SalaryBody(BaseModel):
    country: str | None = None
    experience_level: str | None = None
    technologies: list[str] = []


@salary_router.get("/estimate")
async def salary_estimate_get(
    user: CurrentUser,
    db: DbSession,
    job_id: str | None = None,
    country: str | None = None,
    experience_level: str | None = None,
) -> dict:
    if job_id:
        return await _estimate_for_job(db, job_id)
    return SalaryEstimator().estimate(country=country, experience_level=experience_level, technologies=[])


@salary_router.post("/estimate")
async def salary_estimate_post(user: CurrentUser, db: DbSession, body: SalaryBody) -> dict:
    return SalaryEstimator().estimate(
        country=body.country,
        experience_level=body.experience_level,
        technologies=body.technologies,
    )


async def _estimate_for_job(db, job_id: str) -> dict:
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, detail="Job not found")
    techs: list[str] = []
    if job.technology_stack:
        try:
            parsed = json.loads(job.technology_stack)
            techs = parsed if isinstance(parsed, list) else extract_skills(job.technology_stack)
        except json.JSONDecodeError:
            techs = extract_skills(job.technology_stack)
    est = SalaryEstimator().estimate(
        country=job.country,
        experience_level=job.experience_level,
        technologies=techs,
    )
    if job.salary_min is None:
        job.salary_min = est["min"]
        job.salary_max = est["max"]
        job.salary_currency = est["currency"]
        job.salary_estimated = True
        await db.flush()
    return est


@salary_router.get("/insights")
async def salary_insights(user: CurrentUser, db: DbSession) -> list[dict]:
    result = await db.execute(select(Job).where(Job.is_active.is_(True)).limit(200))
    jobs = result.scalars().all()
    counts: dict[str, dict] = {}
    for job in jobs:
        techs = extract_skills(_job_blob(job))
        mid = None
        if job.salary_min is not None and job.salary_max is not None:
            mid = float((job.salary_min + job.salary_max) / 2)
        for t in techs[:6]:
            row = counts.setdefault(
                t,
                {"technology": t, "demand_score": 0, "avg_salary": 0.0, "currency": "USD", "country": "Global", "job_count": 0, "_sum": 0.0},
            )
            row["job_count"] += 1
            row["demand_score"] += 1
            if mid:
                row["_sum"] += mid
                row["currency"] = job.salary_currency or "USD"
    out = []
    for row in counts.values():
        avg = row["_sum"] / row["job_count"] if row["job_count"] and row["_sum"] else 0
        out.append(
            {
                "technology": row["technology"],
                "demand_score": row["demand_score"],
                "avg_salary": round(avg) if avg else 0,
                "currency": row["currency"],
                "country": "Global",
                "job_count": row["job_count"],
            }
        )
    out.sort(key=lambda x: x["demand_score"], reverse=True)
    return out[:20]


@gap_router.get("/job/{job_id}")
async def skill_gap(job_id: str, user: CurrentUser, db: DbSession) -> list[dict]:
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, detail="Job not found")
    resume = await _primary_resume(db, user.id)
    if resume is None:
        raise HTTPException(400, detail="Upload a resume first")
    return SkillGapEngine().analyze(resume.raw_text or "", _job_blob(job), parse_json_list(resume.skills))


class JobIdBody(BaseModel):
    job_id: str


@ai_router.post("/cover-letter")
async def cover_letter(data: JobIdBody, user: CurrentUser, db: DbSession) -> dict:
    result = await db.execute(
        select(Job).options(selectinload(Job.company)).where(Job.id == data.job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(404, detail="Job not found")
    resume = await _primary_resume(db, user.id)
    company = job.company.name if job.company else "the company"
    return AIContentService().cover_letter(
        job_title=job.title,
        company=company,
        job_text=_job_blob(job),
        resume_text=(resume.raw_text if resume else "") or user.full_name or "",
    )


@ai_router.post("/optimize-resume")
async def optimize_resume(data: JobIdBody, user: CurrentUser, db: DbSession) -> dict:
    job = await db.get(Job, data.job_id)
    if job is None:
        raise HTTPException(404, detail="Job not found")
    resume = await _primary_resume(db, user.id)
    if resume is None or not resume.raw_text:
        raise HTTPException(400, detail="Upload a resume first")
    return AIContentService().optimize_resume(
        resume_text=resume.raw_text, job_text=_job_blob(job), job_title=job.title
    )


@ai_router.post("/optimize-resume/pdf")
async def optimize_resume_pdf(data: JobIdBody, user: CurrentUser, db: DbSession) -> Response:
    """Optimize resume for a job and return a downloadable PDF."""
    job = await db.get(Job, data.job_id)
    if job is None:
        raise HTTPException(404, detail="Job not found")
    resume = await _primary_resume(db, user.id)
    if resume is None or not resume.raw_text:
        raise HTTPException(400, detail="Upload a resume first")

    company = job.company.name if job.company else "Target Company"
    result = AIContentService().optimize_resume(
        resume_text=resume.raw_text, job_text=_job_blob(job), job_title=job.title
    )
    pdf_bytes = build_resume_pdf(
        title=result["optimized_resume"].splitlines()[0][:80] if result.get("optimized_resume") else user.full_name or "Resume",
        subtitle=f"Tailored for {job.title} at {company}",
        resume_text=result["optimized_resume"],
    )
    filename = f"resume-{job.title[:40].replace(' ', '-').lower()}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@ai_router.get("/interview-prep")
async def interview_prep(
    user: CurrentUser, db: DbSession, job_id: str | None = None, role: str | None = None
) -> dict:
    role_contexts = {
        "java": "Java Spring Boot backend engineer, REST APIs, JPA, SQL, microservices",
        "python": "Python backend engineer, FastAPI, Django, testing, SQL, async programming",
        "qa": "QA engineer, test automation, API testing, regression, CI/CD, Selenium",
        "project management": "technical project manager, Agile, delivery, risk, stakeholders, metrics",
        "ai": "AI/ML engineer, Python, model evaluation, data pipelines, LLM applications",
    }
    normalized_role = (role or "java").strip().lower()
    job_title = role.title() if role else None
    job_text = role_contexts.get(normalized_role, role_contexts["java"])
    if job_id:
        job = await db.get(Job, job_id)
        if job:
            job_title = job.title
            job_text = _job_blob(job)
    return AIContentService().interview_prep(job_title=job_title, job_text=job_text)


class InterviewAnswerBody(BaseModel):
    question: str
    answer: str
    role: str | None = None


@ai_router.post("/interview-critique")
async def interview_critique(
    data: InterviewAnswerBody, user: CurrentUser, db: DbSession
) -> dict:
    if len(data.answer.strip()) < 20:
        raise HTTPException(400, detail="Write at least a few sentences before requesting feedback")
    return AIContentService().critique_interview_answer(
        question=data.question.strip(),
        answer=data.answer.strip(),
        role=data.role,
    )


@ai_router.post("/application-pack/pdf")
async def application_pack_pdf(
    data: JobIdBody, user: CurrentUser, db: DbSession
) -> Response:
    result = await db.execute(
        select(Job).options(selectinload(Job.company)).where(Job.id == data.job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(404, detail="Job not found")
    resume = await _primary_resume(db, user.id)
    if resume is None or not resume.raw_text:
        raise HTTPException(400, detail="Upload a primary resume first")

    service = AIContentService()
    company = job.company.name if job.company else "Target Company"
    optimized = service.optimize_resume(
        resume_text=resume.raw_text, job_text=_job_blob(job), job_title=job.title
    )
    letter = service.cover_letter(
        job_title=job.title,
        company=company,
        job_text=_job_blob(job),
        resume_text=resume.raw_text,
    )
    match = ResumeMatchEngine().score(
        optimized["optimized_resume"], _job_blob(job), parse_json_list(resume.skills)
    )
    pdf_bytes = build_application_pack_pdf(
        candidate=user.full_name or "Candidate",
        job_title=job.title,
        company=company,
        match_score=float(match["overall"]),
        resume_text=optimized["optimized_resume"],
        cover_letter=letter["content"],
        strengths=match.get("strengths", []),
        missing_skills=match.get("missing_skills", []),
    )
    safe_title = "".join(ch for ch in job.title[:40] if ch.isalnum() or ch in " -_").strip()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="application-pack-{safe_title.replace(" ", "-").lower()}.pdf"'
        },
    )
