"""Remotive public API connector."""

import re
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


class RemotiveConnector(JobSourceConnector):
    name = "remotive"
    API_URL = "https://remotive.com/api/remote-jobs"

    async def fetch(self, query: str = "java", limit: int = 50) -> list[RawJob]:
        params = {"search": "java", "category": "software-dev", "limit": min(limit * 3, 100)}
        headers = {"User-Agent": "JavaCareerAI/1.0"}
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            response = await client.get(self.API_URL, params=params)
            response.raise_for_status()
            payload = response.json()

        jobs: list[RawJob] = []
        for item in payload.get("jobs", []):
            title = item.get("title") or ""
            description = item.get("description") or ""
            if not is_java_related_job(title, description):
                continue

            salary_text = item.get("salary") or ""
            salary_min, salary_max = self._parse_salary(salary_text)
            posted_raw = item.get("publication_date")
            posted_at = None
            if posted_raw:
                try:
                    posted_at = datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
                except ValueError:
                    posted_at = None

            location = item.get("candidate_required_location") or "Remote"
            blob = f"{title} {description} {location}"
            jobs.append(
                RawJob(
                    source=self.name,
                    external_id=str(item.get("id")),
                    title=title,
                    description=description,
                    company_name=item.get("company_name"),
                    company_logo=item.get("company_logo"),
                    location_raw=location,
                    country=location if len(str(location)) < 64 else None,
                    work_mode=detect_work_mode(blob) or "remote",
                    employment_type=(item.get("job_type") or "").replace("-", "_") or None,
                    experience_level=detect_experience_level(title, description),
                    visa_sponsorship=detect_visa_sponsorship(blob),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    apply_url=item.get("url"),
                    source_url=item.get("url"),
                    posted_at=posted_at,
                    technology_stack=item.get("tags") or [],
                )
            )
            if len(jobs) >= limit:
                break
        return jobs

    @staticmethod
    def _parse_salary(text: str) -> tuple[Decimal | None, Decimal | None]:
        nums = re.findall(r"[\d,]+", text.replace("k", "000").replace("K", "000"))
        values: list[Decimal] = []
        for n in nums:
            try:
                values.append(Decimal(n.replace(",", "")))
            except Exception:
                continue
        if len(values) >= 2:
            return values[0], values[1]
        if len(values) == 1:
            return values[0], values[0]
        return None, None
