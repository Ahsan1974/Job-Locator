"""Salary estimation without external services."""

from __future__ import annotations

from app.domain.skills import DEFAULT_SALARY, SALARY_BASE


class SalaryEstimator:
    TECH_BONUS = {
        "Kafka": 0.04,
        "Kubernetes": 0.05,
        "AWS": 0.04,
        "Azure": 0.03,
        "GCP": 0.03,
        "Spring Cloud": 0.03,
        "Microservices": 0.02,
    }

    def estimate(
        self,
        *,
        country: str | None = None,
        experience_level: str | None = None,
        technologies: list[str] | None = None,
    ) -> dict:
        country_key = country or "Remote"
        level = (experience_level or "mid").lower()
        table = SALARY_BASE.get(country_key) or SALARY_BASE.get(
            next((k for k in SALARY_BASE if k.lower() == country_key.lower()), ""),
            DEFAULT_SALARY,
        )
        lo, hi, currency = table.get(level, table.get("mid", (80000, 120000, "USD")))
        bonus = 1.0
        techs = technologies or []
        for t in techs:
            bonus += self.TECH_BONUS.get(t, 0)
        lo, hi = int(lo * bonus), int(hi * bonus)
        median = (lo + hi) // 2
        return {
            "min": lo,
            "max": hi,
            "median": median,
            "currency": currency,
            "country": country_key,
            "experience_level": level,
            "technologies": techs,
            "confidence": 0.72,
        }
