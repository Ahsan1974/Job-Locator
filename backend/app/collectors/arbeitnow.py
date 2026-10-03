"""Arbeitnow public API — European tech jobs including Java."""

from datetime import datetime
from decimal import Decimal

import httpx

from app.collectors.base import JobSourceConnector, RawJob
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_job,
)


class ArbeitnowConnector(JobSourceConnector):
    name = "arbeitnow"
    API_URL = "https://www.arbeitnow.com/api/job-board-api"

    async def fetch(self, query: str = "java", limit: int = 50) -> list[RawJob]:
        headers = {"User-Agent": "JavaCareerAI/1.0"}
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            response = await client.get(self.API_URL)
            response.raise_for_status()
            payload = response.json()

        jobs: list[RawJob] = []
        for item in payload.get("data", []):
            title = item.get("title") or ""
            description = item.get("description") or ""
            if not is_java_related_job(title, description):
                continue

            tags = item.get("tags") or []
            location = item.get("location") or ""
            created = item.get("created_at")
            posted_at = None
            if created:
                try:
                    posted_at = datetime.fromtimestamp(created) if isinstance(created, (int, float)) else None
                except (OSError, ValueError):
                    posted_at = None

            blob = f"{title} {description} {location} {' '.join(tags)}"
            jobs.append(
                RawJob(
                    source=self.name,
                    external_id=str(item.get("slug") or item.get("url")),
                    title=title,
                    description=description,
                    company_name=item.get("company_name"),
                    location_raw=location,
                    country=location.split(",")[-1].strip() if location else None,
                    work_mode="remote" if item.get("remote") else detect_work_mode(blob),
                    experience_level=detect_experience_level(title, description),
                    visa_sponsorship=detect_visa_sponsorship(blob)
                    or ("visa" in [t.lower() for t in tags]),
                    apply_url=item.get("url"),
                    source_url=item.get("url"),
                    posted_at=posted_at,
                    technology_stack=[str(t) for t in tags],
                    salary_min=None,
                    salary_max=None,
                    salary_currency="EUR",
                )
            )
            if len(jobs) >= limit:
                break
        return jobs
