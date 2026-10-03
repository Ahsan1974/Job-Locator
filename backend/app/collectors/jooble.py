"""Jooble REST API — aggregates jobs from Indeed, LinkedIn, Monster, etc."""

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

JOOBLE_KEYWORDS = (
    "java developer spring boot",
    "python developer",
    "machine learning engineer",
    "ai engineer",
    "java backend engineer",
    "spring boot developer",
)

# Country + major cities for broader coverage (Jooble works better with cities)
JOOBLE_LOCATIONS: tuple[tuple[str, str | None], ...] = (
    ("United States", None),
    ("United Kingdom", None),
    ("Germany", None),
    ("Canada", None),
    ("Australia", None),
    ("Pakistan", "Lahore"),
    ("Pakistan", "Karachi"),
    ("Pakistan", "Islamabad"),
    ("United Arab Emirates", "Dubai"),
    ("Singapore", None),
    ("Netherlands", None),
    ("Ireland", None),
    ("France", None),
    ("Sweden", None),
    ("Switzerland", None),
    ("Remote", None),
    ("", None),  # worldwide
)


class JoobleConnector(JobSourceConnector):
    name = "jooble"

    async def fetch(self, query: str = "java developer spring boot", limit: int = 50) -> list[RawJob]:
        settings = get_settings()
        if not settings.jooble_api_key:
            logger.info("Jooble skipped — set JOOBLE_API_KEY in .env")
            return []

        jobs: list[RawJob] = []
        seen: set[str] = set()
        per_keyword = max(8, limit // len(JOOBLE_KEYWORDS))
        keyword_counts: dict[str, int] = {}
        headers = {"User-Agent": "JavaCareerAI/1.0", "Content-Type": "application/json"}
        url = f"https://jooble.org/api/{settings.jooble_api_key}"

        async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
            for keywords in JOOBLE_KEYWORDS:
                if len(jobs) >= limit:
                    break
                for country, city in JOOBLE_LOCATIONS:
                    if len(jobs) >= limit or keyword_counts.get(keywords, 0) >= per_keyword:
                        break
                    location = city or country
                    for page in range(1, 2):
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
                            logger.debug("Jooble %s/%s page %s failed: %s", country, keywords, page, exc)
                            break

                        batch = payload.get("jobs", [])
                        if not batch:
                            break

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

                            country_name = normalize_country(country) if country else None
                            if city and country_name:
                                country_name = country_name if country != "Remote" else "Remote"

                            jobs.append(
                                RawJob(
                                    source=self.name,
                                    external_id=ext_id,
                                    title=title,
                                    description=description,
                                    company_name=item.get("company"),
                                    location_raw=loc,
                                    city=city,
                                    country=normalize_country(loc) or country_name,
                                    work_mode=detect_work_mode(blob) or (
                                        "remote" if "remote" in str(loc).lower() else None
                                    ),
                                    employment_type=(item.get("type") or "").replace("-", "_") or None,
                                    experience_level=detect_experience_level(title, description),
                                    visa_sponsorship=detect_visa_sponsorship(blob),
                                    apply_url=link,
                                    source_url=link,
                                    posted_at=posted_at,
                                    salary_min=salary_min,
                                    salary_max=salary_max,
                                )
                            )
                            keyword_counts[keywords] = keyword_counts.get(keywords, 0) + 1
                            if len(jobs) >= limit or keyword_counts[keywords] >= per_keyword:
                                break

        logger.info("Jooble fetched %s Java jobs", len(jobs))
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
