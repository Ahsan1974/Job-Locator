"""Working Nomads public JSON API."""

import logging
from datetime import datetime

import httpx

from app.collectors.base import JobSourceConnector, RawJob
from app.domain.country import normalize_country
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_job,
)

logger = logging.getLogger(__name__)

API_URLS = (
    "https://www.workingnomads.com/api/exposed_jobs/",
    "https://workingnomads.com/api/exposed_jobs/",
)


class WorkingNomadsConnector(JobSourceConnector):
    name = "workingnomads"

    async def fetch(self, query: str = "java", limit: int = 50) -> list[RawJob]:
        data = await self._fetch_payload()
        if not data:
            return []

        jobs: list[RawJob] = []
        for item in data:
            title = item.get("title") or ""
            description = item.get("description") or ""
            if not is_java_related_job(title, description):
                continue

            url = item.get("url")
            company = item.get("company_name") or item.get("company")
            category = item.get("category") or ""
            location = item.get("location") or "Remote"
            posted_at = None
            if item.get("pub_date"):
                try:
                    posted_at = datetime.fromisoformat(str(item["pub_date"]).replace("Z", "+00:00"))
                except ValueError:
                    posted_at = None

            blob = f"{title} {description} {location} {category}"
            jobs.append(
                RawJob(
                    source=self.name,
                    external_id=str(item.get("id") or url or title),
                    title=title,
                    description=description,
                    company_name=company,
                    company_logo=item.get("company_logo"),
                    location_raw=location,
                    country=normalize_country(location) or "Remote",
                    work_mode=detect_work_mode(blob) or "remote",
                    experience_level=detect_experience_level(title, description),
                    visa_sponsorship=detect_visa_sponsorship(blob),
                    apply_url=url,
                    source_url=url,
                    posted_at=posted_at,
                    technology_stack=[category] if category else [],
                )
            )
            if len(jobs) >= limit:
                break
        return jobs

    async def _fetch_payload(self) -> list[dict]:
        headers = {"User-Agent": "JavaCareerAI/1.0 (personal job aggregator)"}
        last_error: Exception | None = None

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=20.0),
            headers=headers,
            follow_redirects=True,
        ) as client:
            for url in API_URLS:
                for attempt in range(2):
                    try:
                        response = await client.get(url)
                        response.raise_for_status()
                        payload = response.json()
                        if isinstance(payload, list):
                            return payload
                        return payload.get("jobs", payload.get("data", []))
                    except (httpx.ConnectError, httpx.TimeoutException, OSError) as exc:
                        last_error = exc
                        logger.debug(
                            "Working Nomads attempt %s for %s failed: %s",
                            attempt + 1,
                            url,
                            exc,
                        )
                    except httpx.HTTPStatusError as exc:
                        last_error = exc
                        break

        if last_error:
            logger.warning("Working Nomads unavailable (skipped): %s", last_error)
        return []
