"""USA, Germany, and UAE-focused Java jobs via Jooble (when API key is set)."""

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

# keywords, location, country label, optional work_mode override
REGIONAL_SEARCHES: tuple[tuple[str, str, str, str | None], ...] = (
    # United States — major tech hubs + nationwide
    ("java developer spring boot", "San Francisco", "United States", None),
    ("java developer", "New York", "United States", None),
    ("java developer", "Seattle", "United States", None),
    ("java developer", "Austin", "United States", None),
    ("java developer", "Chicago", "United States", None),
    ("java backend engineer", "Boston", "United States", None),
    ("java developer", "Denver", "United States", None),
    ("java developer", "United States", "United States", None),
    ("java developer visa sponsorship", "United States", "United States", None),
    ("java developer h1b", "United States", "United States", None),
    ("java spring boot remote", "United States", "United States", "remote"),
    ("python developer", "United States", "United States", None),
    ("python developer", "New York", "United States", None),
    ("machine learning engineer", "United States", "United States", None),
    ("ai engineer", "San Francisco", "United States", None),
    ("python developer", "Berlin", "Germany", None),
    ("machine learning engineer", "Germany", "Germany", None),
    ("python developer", "Dubai", "United Arab Emirates", None),
    ("ai engineer", "United Arab Emirates", "United Arab Emirates", None),
    ("python developer remote", "Remote", "Remote", "remote"),
    # Germany — onsite + major cities
    ("java entwickler spring", "Berlin", "Germany", None),
    ("java developer", "Munich", "Germany", None),
    ("java developer", "Frankfurt", "Germany", None),
    ("java developer", "Hamburg", "Germany", None),
    ("java developer", "Germany", "Germany", None),
    ("java developer onsite", "Germany", "Germany", "onsite"),
    # UAE / Dubai
    ("java developer", "Dubai", "United Arab Emirates", None),
    ("java developer", "Abu Dhabi", "United Arab Emirates", None),
    ("java spring boot developer", "United Arab Emirates", "United Arab Emirates", None),
    ("java developer visa sponsorship", "Dubai", "United Arab Emirates", None),
    # Global remote + visa
    ("java developer remote", "", "Remote", "remote"),
    ("java spring boot remote", "Remote", "Remote", "remote"),
    ("java developer visa sponsorship remote", "", "Remote", "remote"),
)


class RegionalJobsConnector(JobSourceConnector):
    name = "regional"

    async def fetch(self, query: str = "java developer", limit: int = 80) -> list[RawJob]:
        settings = get_settings()
        if not settings.jooble_api_key:
            return []

        jobs: list[RawJob] = []
        seen: set[str] = set()
        headers = {"User-Agent": "JavaCareerAI/1.0", "Content-Type": "application/json"}
        url = f"https://jooble.org/api/{settings.jooble_api_key}"

        async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
            for keywords, location, country, mode_override in REGIONAL_SEARCHES:
                if len(jobs) >= limit:
                    break
                for page in range(1, 3):
                    if len(jobs) >= limit:
                        break
                    body = {
                        "keywords": keywords,
                        "location": location,
                        "page": str(page),
                        "companysearch": "false",
                    }
                    try:
                        response = await client.post(url, json=body)
                        response.raise_for_status()
                        payload = response.json()
                    except Exception as exc:
                        logger.debug("Regional %s/%s failed: %s", country, keywords, exc)
                        break

                    batch = payload.get("jobs", [])
                    if not batch:
                        break

                    visa_query = "visa" in keywords.lower() or "h1b" in keywords.lower()
                    for item in batch:
                        title = item.get("title") or ""
                        description = item.get("snippet") or ""
                        if not is_java_related_from_aggregator(title, description):
                            continue
                        link = item.get("link") or ""
                        ext_id = str(item.get("id") or link or title)
                        if ext_id in seen:
                            continue
                        seen.add(ext_id)

                        loc = item.get("location") or location or None
                        blob = f"{title} {description} {loc or ''}"
                        salary_min, salary_max = self._parse_salary(item.get("salary") or "")
                        posted_at = self._parse_date(item.get("updated"))
                        work_mode = mode_override or detect_work_mode(blob) or (
                            "remote" if country == "Remote" else None
                        )
                        visa = detect_visa_sponsorship(blob) or visa_query

                        jobs.append(
                            RawJob(
                                source=self.name,
                                external_id=ext_id,
                                title=title,
                                description=description,
                                company_name=item.get("company"),
                                location_raw=loc,
                                city=location.split(",")[0] if location and "," not in country else None,
                                country=normalize_country(country) if country != "Remote" else "Remote",
                                work_mode=work_mode,
                                employment_type=(item.get("type") or "").replace("-", "_") or None,
                                experience_level=detect_experience_level(title, description),
                                visa_sponsorship=visa,
                                apply_url=link,
                                source_url=link,
                                posted_at=posted_at,
                                salary_min=salary_min,
                                salary_max=salary_max,
                            )
                        )
                        if len(jobs) >= limit:
                            break

        logger.info("Regional (US/DE/UAE) fetched %s Java jobs", len(jobs))
        return jobs

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _parse_salary(text: str) -> tuple[Decimal | None, Decimal | None]:
        if not text:
            return None, None
        nums = []
        for part in text.replace(",", "").split():
            cleaned = "".join(c for c in part if c.isdigit() or c == ".")
            if cleaned:
                try:
                    nums.append(Decimal(cleaned))
                except Exception:
                    continue
        if len(nums) >= 2:
            return nums[0], nums[1]
        if len(nums) == 1:
            return nums[0], nums[0]
        return None, None
