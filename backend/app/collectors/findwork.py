"""Findwork.dev public API."""

from datetime import datetime

import httpx

from app.collectors.base import JobSourceConnector, RawJob
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_job,
)


class FindworkConnector(JobSourceConnector):
    name = "findwork"
    API_URL = "https://findwork.dev/api/jobs/"

    async def fetch(self, query: str = "java", limit: int = 50) -> list[RawJob]:
        params = {"search": "java spring", "location": "remote", "page": 1}
        headers = {"User-Agent": "JavaCareerAI/1.0"}
        try:
            async with httpx.AsyncClient(timeout=45.0, headers=headers) as client:
                response = await client.get(self.API_URL, params=params)
                if response.status_code == 401:
                    return []  # requires API token at findwork.dev
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError:
            return []

        jobs: list[RawJob] = []
        for item in payload.get("results", []):
            title = item.get("role") or item.get("title") or ""
            description = item.get("description") or ""
            if not is_java_related_job(title, description):
                continue
            url = item.get("url") or item.get("application_url")
            company = item.get("company_name")
            keywords = item.get("keywords") or []
            posted_at = None
            if item.get("date_posted"):
                try:
                    posted_at = datetime.fromisoformat(str(item["date_posted"]).replace("Z", "+00:00"))
                except ValueError:
                    posted_at = None
            blob = f"{title} {description} {' '.join(keywords)}"
            jobs.append(
                RawJob(
                    source=self.name,
                    external_id=str(item.get("id") or url),
                    title=title,
                    description=description,
                    company_name=company,
                    location_raw=item.get("location") or "Remote",
                    country="Remote",
                    work_mode=detect_work_mode(blob) or "remote",
                    experience_level=detect_experience_level(title, description),
                    visa_sponsorship=detect_visa_sponsorship(blob),
                    apply_url=url,
                    source_url=url,
                    posted_at=posted_at,
                    technology_stack=[str(k) for k in keywords],
                    employment_type=item.get("employment_type"),
                )
            )
            if len(jobs) >= limit:
                break
        return jobs
