"""Himalayas public jobs API."""

from datetime import datetime

import httpx

from app.collectors.base import JobSourceConnector, RawJob
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_job,
)


class HimalayasConnector(JobSourceConnector):
    name = "himalayas"
    API_URL = "https://himalayas.app/jobs/api"

    async def fetch(self, query: str = "java", limit: int = 50) -> list[RawJob]:
        params = {"limit": min(limit * 3, 150)}
        headers = {"User-Agent": "JavaCareerAI/1.0"}
        async with httpx.AsyncClient(timeout=45.0, headers=headers) as client:
            response = await client.get(self.API_URL, params=params)
            response.raise_for_status()
            payload = response.json()

        items = payload if isinstance(payload, list) else payload.get("jobs", payload.get("data", []))
        jobs: list[RawJob] = []
        for item in items:
            title = item.get("title") or ""
            description = item.get("description") or item.get("excerpt") or ""
            if not is_java_related_job(title, description):
                continue
            url = item.get("applicationLink") or item.get("url") or item.get("slug")
            if url and not str(url).startswith("http"):
                url = f"https://himalayas.app/jobs/{url}"
            company = item.get("companyName") or (item.get("company") or {}).get("name")
            loc = item.get("locationRestrictions") or item.get("location") or "Remote"
            if isinstance(loc, list):
                loc = ", ".join(str(x) for x in loc)
            posted_at = None
            if item.get("pubDate"):
                try:
                    posted_at = datetime.fromisoformat(str(item["pubDate"]).replace("Z", "+00:00"))
                except ValueError:
                    posted_at = None
            blob = f"{title} {description} {loc}"
            jobs.append(
                RawJob(
                    source=self.name,
                    external_id=str(item.get("id") or url or title),
                    title=title,
                    description=description,
                    company_name=company,
                    company_logo=(item.get("company") or {}).get("logoUrl"),
                    location_raw=str(loc),
                    country="Remote",
                    work_mode=detect_work_mode(blob) or "remote",
                    experience_level=detect_experience_level(title, description),
                    visa_sponsorship=detect_visa_sponsorship(blob),
                    apply_url=url,
                    source_url=url,
                    posted_at=posted_at,
                    technology_stack=item.get("categories") or [],
                )
            )
            if len(jobs) >= limit:
                break
        return jobs
