"""USAJobs official API connector."""

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


class USAJobsConnector(JobSourceConnector):
    name = "usajobs"
    API_URL = "https://data.usajobs.gov/api/search"

    async def fetch(self, query: str = "Java Developer", limit: int = 50) -> list[RawJob]:
        settings = get_settings()
        if not settings.usajobs_api_key:
            return []

        headers = {
            "Host": "data.usajobs.gov",
            "User-Agent": settings.usajobs_user_agent,
            "Authorization-Key": settings.usajobs_api_key,
        }
        params = {"Keyword": query, "ResultsPerPage": min(limit, 50), "Page": 1}
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            response = await client.get(self.API_URL, params=params)
            response.raise_for_status()
            payload = response.json()

        jobs: list[RawJob] = []
        results = payload.get("SearchResult", {}).get("SearchResultItems", [])
        for item in results:
            descriptor = item.get("MatchedObjectDescriptor", {})
            title = descriptor.get("PositionTitle") or ""
            details = descriptor.get("UserArea", {}).get("Details", {})
            description = details.get("JobSummary") or descriptor.get("QualificationSummary") or ""
            if not is_java_related_job(title, description):
                continue

            locations = descriptor.get("PositionLocation") or []
            loc = locations[0] if locations else {}
            remun = (descriptor.get("PositionRemuneration") or [{}])[0]
            salary_min = remun.get("MinimumRange")
            salary_max = remun.get("MaximumRange")
            posted_raw = descriptor.get("PublicationStartDate")
            posted_at = None
            if posted_raw:
                try:
                    posted_at = datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
                except ValueError:
                    posted_at = None

            blob = f"{title} {description}"
            jobs.append(
                RawJob(
                    source=self.name,
                    external_id=str(descriptor.get("PositionID") or item.get("MatchedObjectId")),
                    title=title,
                    description=description,
                    company_name=descriptor.get("OrganizationName") or "US Federal Government",
                    country="USA",
                    city=loc.get("CityName"),
                    location_raw=loc.get("LocationName"),
                    work_mode=detect_work_mode(blob) or "onsite",
                    employment_type="full_time",
                    experience_level=detect_experience_level(title, description),
                    visa_sponsorship=detect_visa_sponsorship(blob),
                    salary_min=Decimal(str(salary_min)) if salary_min else None,
                    salary_max=Decimal(str(salary_max)) if salary_max else None,
                    salary_currency="USD",
                    salary_period="year",
                    apply_url=descriptor.get("PositionURI"),
                    source_url=descriptor.get("PositionURI"),
                    posted_at=posted_at,
                )
            )
            if len(jobs) >= limit:
                break
        return jobs
