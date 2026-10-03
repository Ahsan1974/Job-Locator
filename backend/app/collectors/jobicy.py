"""Jobicy public API — remote Java jobs."""

from datetime import datetime
from decimal import Decimal

import httpx

from app.collectors.base import JobSourceConnector, RawJob
from app.domain.country import normalize_country
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_job,
)


class JobicyConnector(JobSourceConnector):
    name = "jobicy"
    API_URL = "https://jobicy.com/api/v2/remote-jobs"

    async def fetch(self, query: str = "java", limit: int = 50) -> list[RawJob]:
        tags = ("java", "spring", "backend", "jvm")
        jobs: list[RawJob] = []
        seen: set[str] = set()
        per_tag = max(15, limit // len(tags))
        headers = {"User-Agent": "JavaCareerAI/1.0"}

        async with httpx.AsyncClient(timeout=45.0, headers=headers) as client:
            for tag in tags:
                if len(jobs) >= limit:
                    break
                params = {"count": min(per_tag * 2, 100), "tag": tag}
                try:
                    response = await client.get(self.API_URL, params=params)
                    response.raise_for_status()
                    payload = response.json()
                except Exception:
                    continue

                for item in payload.get("jobs", []):
                    title = item.get("jobTitle") or item.get("title") or ""
                    description = item.get("jobDescription") or item.get("description") or ""
                    if not is_java_related_job(title, description):
                        continue
                    url = item.get("url") or item.get("jobUrl")
                    ext_id = str(item.get("id") or url or title)
                    if ext_id in seen:
                        continue
                    seen.add(ext_id)
                    geo = item.get("jobGeo") or item.get("geo") or "Remote"
                    company = item.get("companyName") or item.get("company")
                    posted = item.get("pubDate") or item.get("date")
                    posted_at = None
                    if posted:
                        try:
                            posted_at = datetime.fromisoformat(str(posted).replace("Z", "+00:00"))
                        except ValueError:
                            posted_at = None
                    blob = f"{title} {description} {geo}"
                    jobs.append(
                        RawJob(
                            source=self.name,
                            external_id=ext_id,
                            title=title,
                            description=description,
                            company_name=company,
                            company_logo=item.get("companyLogo"),
                            location_raw=geo,
                            country=normalize_country(geo) or "Remote",
                            work_mode=detect_work_mode(blob) or "remote",
                            experience_level=detect_experience_level(title, description),
                            visa_sponsorship=detect_visa_sponsorship(blob),
                            apply_url=url,
                            source_url=url,
                            posted_at=posted_at,
                            salary_min=None,
                            salary_max=None,
                            salary_currency="USD",
                        )
                    )
                    if len(jobs) >= limit:
                        break
        return jobs
