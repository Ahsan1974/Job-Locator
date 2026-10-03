"""RemoteOK public API connector."""

from datetime import UTC, datetime
from decimal import Decimal

import httpx

from app.collectors.base import JobSourceConnector, RawJob
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_job,
    normalize_work_mode,
)


class RemoteOKConnector(JobSourceConnector):
    name = "remoteok"
    API_URL = "https://remoteok.com/api"

    async def fetch(self, query: str = "Java Spring Boot", limit: int = 50) -> list[RawJob]:
        headers = {"User-Agent": "JavaCareerAI/1.0 (personal job aggregator)"}
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            response = await client.get(self.API_URL)
            response.raise_for_status()
            data = response.json()

        jobs: list[RawJob] = []
        for item in data:
            if not isinstance(item, dict) or "id" not in item:
                continue
            title = item.get("position") or item.get("title") or ""
            description = item.get("description") or ""
            if not is_java_related_job(title, description):
                continue

            tags = item.get("tags") or []
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            epoch = item.get("epoch") or item.get("date")
            posted_at = None
            if isinstance(epoch, (int, float)):
                posted_at = datetime.fromtimestamp(epoch, tz=UTC)

            location = item.get("location") or "Worldwide"
            blob = f"{title} {description} {location}"
            jobs.append(
                RawJob(
                    source=self.name,
                    external_id=str(item["id"]),
                    title=title,
                    description=description,
                    company_name=item.get("company"),
                    company_logo=item.get("company_logo"),
                    location_raw=location,
                    country="Remote" if "worldwide" in str(location).lower() else None,
                    work_mode=normalize_work_mode(blob, fallback="remote", location=location),
                    experience_level=detect_experience_level(title, description),
                    visa_sponsorship=detect_visa_sponsorship(blob),
                    salary_min=Decimal(str(salary_min)) if salary_min else None,
                    salary_max=Decimal(str(salary_max)) if salary_max else None,
                    apply_url=item.get("url") or item.get("apply_url"),
                    source_url=item.get("url"),
                    posted_at=posted_at,
                    technology_stack=[str(t) for t in tags] if isinstance(tags, list) else [],
                )
            )
            if len(jobs) >= limit:
                break
        return jobs
