"""JSearch API via RapidAPI — optional aggregator."""

import logging
from datetime import datetime
from decimal import Decimal

import httpx

from app.collectors.base import JobSourceConnector, RawJob
from app.core.config import get_settings
from app.domain.country import normalize_country
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_from_aggregator,
)

logger = logging.getLogger(__name__)

JSEARCH_QUERIES = (
    ("java developer spring boot", "United States"),
    ("python developer", "United States"),
    ("machine learning engineer", "United States"),
    ("ai engineer", "Remote"),
    ("python developer", "Germany"),
    ("python developer", "Pakistan"),
    ("python developer", "Dubai"),
    ("java developer remote", "United States"),
    ("java developer visa sponsorship", "United States"),
    ("java developer", "San Francisco"),
    ("java developer", "New York"),
    ("java developer", "Germany"),
    ("java developer Berlin", "Germany"),
    ("java developer Munich", "Germany"),
    ("java developer onsite", "Germany"),
    ("java developer", "United Kingdom"),
    ("java developer", "Pakistan"),
    ("java developer", "Canada"),
    ("java developer", "Dubai"),
    ("java developer", "United Arab Emirates"),
    ("java developer remote", "Remote"),
    ("java developer visa sponsorship", "Dubai"),
)


class JSearchConnector(JobSourceConnector):
    name = "jsearch"
    API_URL = "https://jsearch.p.rapidapi.com/search"

    async def fetch(self, query: str = "java developer", limit: int = 50) -> list[RawJob]:
        settings = get_settings()
        if not settings.jsearch_rapidapi_key:
            return []

        jobs: list[RawJob] = []
        seen: set[str] = set()
        headers = {
            "User-Agent": "JavaCareerAI/1.0",
            "X-RapidAPI-Key": settings.jsearch_rapidapi_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }

        async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
            for keywords, country in JSEARCH_QUERIES:
                if len(jobs) >= limit:
                    break
                try:
                    response = await client.get(
                        self.API_URL,
                        params={
                            "query": f"{keywords} in {country}",
                            "page": "1",
                            "num_pages": "2",
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                except Exception as exc:
                    logger.debug("JSearch %s failed: %s", country, exc)
                    continue

                for item in payload.get("data", []):
                    title = item.get("job_title") or ""
                    description = item.get("job_description") or item.get("job_highlights", {}).get("Qualifications", [""])[0] if isinstance(item.get("job_highlights"), dict) else ""
                    if isinstance(description, list):
                        description = " ".join(description)
                    if not is_java_related_from_aggregator(title, str(description)):
                        continue
                    ext_id = str(item.get("job_id") or item.get("job_apply_link") or title)
                    if ext_id in seen:
                        continue
                    seen.add(ext_id)

                    loc = item.get("job_city") or item.get("job_country") or country
                    apply_url = item.get("job_apply_link")
                    posted_at = None
                    if item.get("job_posted_at_datetime_utc"):
                        try:
                            posted_at = datetime.fromisoformat(str(item["job_posted_at_datetime_utc"]).replace("Z", "+00:00"))
                        except ValueError:
                            posted_at = None

                    blob = f"{title} {description} {loc}"
                    salary_min = item.get("job_min_salary")
                    salary_max = item.get("job_max_salary")
                    jobs.append(
                        RawJob(
                            source=self.name,
                            external_id=ext_id,
                            title=title,
                            description=str(description)[:5000],
                            company_name=item.get("employer_name"),
                            company_logo=item.get("employer_logo"),
                            location_raw=str(loc),
                            city=item.get("job_city"),
                            country=normalize_country(item.get("job_country") or country),
                            work_mode=detect_work_mode(blob) or ("remote" if item.get("job_is_remote") else None),
                            experience_level=detect_experience_level(title, str(description)),
                            visa_sponsorship=detect_visa_sponsorship(blob),
                            apply_url=apply_url,
                            source_url=apply_url,
                            posted_at=posted_at,
                            salary_min=Decimal(str(salary_min)) if salary_min else None,
                            salary_max=Decimal(str(salary_max)) if salary_max else None,
                            salary_currency=item.get("job_salary_currency") or "USD",
                        )
                    )
                    if len(jobs) >= limit:
                        break
        return jobs
