"""Job recommendation scoring."""

from __future__ import annotations

from decimal import Decimal

from app.services.match_engine import ResumeMatchEngine


class RecommendationEngine:
    def __init__(self) -> None:
        self.matcher = ResumeMatchEngine()

    def score_job(
        self,
        *,
        resume_text: str,
        resume_skills: list[str],
        job_text: str,
        work_mode: str | None,
        visa: bool,
        preferred_modes: list[str] | None = None,
        visa_required: bool = False,
        salary_min: float | None = None,
        salary_expectation: int | None = None,
    ) -> tuple[Decimal, str]:
        match = self.matcher.score(resume_text, job_text, resume_skills)
        score = float(match["overall"])

        if preferred_modes and work_mode and work_mode in preferred_modes:
            score += 5
        if visa_required and visa:
            score += 8
        elif visa_required and not visa:
            score -= 15
        if salary_expectation and salary_min and salary_min >= salary_expectation * 0.85:
            score += 4

        score = max(0.0, min(100.0, score))
        if score >= 80:
            priority = "high"
        elif score >= 60:
            priority = "medium"
        else:
            priority = "low"
        return Decimal(str(round(score, 1))), priority
