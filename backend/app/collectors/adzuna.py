"""Adzuna official API — multi-country Java jobs (requires free API keys)."""

from datetime import datetime
from decimal import Decimal

import httpx

from app.collectors.base import JobSourceConnector, RawJob
from app.core.config import get_settings
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_job,
)

# Adzuna country codes from original spec
ADZUNA_COUNTRIES = ("us", "gb", "de", "ca", "au", "in", "sg", "ae", "nl", "ie", "fr", "at", "ch")


class AdzunaConnector(JobSourceConnector):
    name = "adzuna"

    async def fetch(self, query: str = "java developer spring", limit: int = 50) -> list[RawJob]:
        settings = get_settings()
        if not settings.adzuna_app_id or not settings.adzuna_app_key:
            return []

        jobs: list[RawJob] = []
        per_country = max(5, limit // len(ADZUNA_COUNTRIES))
        headers = {"User-Agent": "JavaCareerAI/1.0"}
        async with httpx.AsyncClient(timeout=45.0, headers=headers) as client:
            for country in ADZUNA_COUNTRIES:
                if len(jobs) >= limit:
                    break
                url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
                params = {
                    "app_id": settings.adzuna_app_id,
                    "app_key": settings.adzuna_app_key,
                    "results_per_page": per_country,
                    "what": "java spring boot developer",
                    "content-type": "application/json",
                }
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    payload = response.json()
                except Exception:
                    continue
                for item in payload.get("results", []):
                    title = item.get("title") or ""
                    description = item.get("description") or ""
                    if not is_java_related_job(title, description):
                        continue
                    loc = item.get("location") or {}
                    city = loc.get("area", [None])[-1] if isinstance(loc.get("area"), list) else None
                    redirect = item.get("redirect_url")
                    company = item.get("company", {}).get("display_name")
                    posted_at = None
                    if item.get("created"):
                        try:
                            posted_at = datetime.fromisoformat(str(item["created"]).replace("Z", "+00:00"))
                        except ValueError:
                            posted_at = None
                    blob = f"{title} {description}"
                    salary_min = item.get("salary_min")
                    salary_max = item.get("salary_max")
                    jobs.append(
                        RawJob(
                            source=self.name,
                            external_id=str(item.get("id")),
                            title=title,
                            description=description,
                            company_name=company,
                            country=country.upper(),
                            city=city,
                            location_raw=loc.get("display_name"),
                            work_mode=detect_work_mode(blob),
                            experience_level=detect_experience_level(title, description),
                            visa_sponsorship=detect_visa_sponsorship(blob),
                            apply_url=redirect,
                            source_url=redirect,
                            posted_at=posted_at,
                            salary_min=Decimal(str(salary_min)) if salary_min else None,
                            salary_max=Decimal(str(salary_max)) if salary_max else None,
                            salary_currency=item.get("salary_currency") or "USD",
                        )
                    )
                    if len(jobs) >= limit:
                        break
        return jobs
