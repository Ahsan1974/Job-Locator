"""Careerjet affiliate API — multi-country Java job search."""

import base64
import logging
from datetime import UTC, datetime
from decimal import Decimal
from email.utils import parsedate_to_datetime

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

CAREERJET_LOCALES = (
    "en_US",
    "en_GB",
    "en_DE",
    "en_CA",
    "en_AU",
    "en_IN",
    "en_SG",
    "en_AE",
    "en_NL",
    "en_IE",
    "en_FR",
    "en_SE",
    "en_CH",
    "en_PK",
)


class CareerjetConnector(JobSourceConnector):
    name = "careerjet"
    API_URL = "https://search.api.careerjet.net/v4/query"

    async def fetch(self, query: str = "java developer spring boot", limit: int = 50) -> list[RawJob]:
        settings = get_settings()
        if not settings.careerjet_api_key:
            logger.info("Careerjet skipped — set CAREERJET_API_KEY in .env")
            return []

        jobs: list[RawJob] = []
        seen: set[str] = set()
        auth = base64.b64encode(f"{settings.careerjet_api_key}:".encode()).decode()
        headers = {
            "User-Agent": "JavaCareerAI/1.0",
            "Authorization": f"Basic {auth}",
            "Referer": settings.app_url or "http://localhost:3000",
        }
        params_base = {
            "keywords": "java developer spring boot",
            "sort": "date",
            "page_size": 50,
            "user_ip": "127.0.0.1",
            "user_agent": "JavaCareerAI/1.0",
        }

        async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
            for locale in CAREERJET_LOCALES:
                if len(jobs) >= limit:
                    break
                for page in range(1, 4):
                    if len(jobs) >= limit:
                        break
                    params = {**params_base, "locale_code": locale, "page": page}
                    try:
                        response = await client.get(self.API_URL, params=params)
                        response.raise_for_status()
                        payload = response.json()
                    except Exception as exc:
                        logger.debug("Careerjet %s page %s failed: %s", locale, page, exc)
                        break

                    if payload.get("type") != "JOBS":
                        break

                    batch = payload.get("jobs", [])
                    if not batch:
                        break

                    for item in batch:
                        title = item.get("title") or ""
                        description = item.get("description") or ""
                        if not is_java_related_from_aggregator(title, description):
                            continue
                        link = item.get("url") or ""
                        ext_id = str(link or title)
                        if ext_id in seen:
                            continue
                        seen.add(ext_id)

                        loc = item.get("locations") or item.get("location") or ""
                        if isinstance(loc, list):
                            loc = ", ".join(str(x) for x in loc)
                        blob = f"{title} {description} {loc}"
                        salary_min = item.get("salary_min")
                        salary_max = item.get("salary_max")
                        posted_at = self._parse_date(item.get("date"))

                        jobs.append(
                            RawJob(
                                source=self.name,
                                external_id=ext_id,
                                title=title,
                                description=description,
                                company_name=item.get("company"),
                                location_raw=str(loc) if loc else None,
                                country=normalize_country(
                                    str(loc).split(",")[-1].strip() if loc else None
                                ),
                                work_mode=detect_work_mode(blob),
                                experience_level=detect_experience_level(title, description),
                                visa_sponsorship=detect_visa_sponsorship(blob),
                                apply_url=link,
                                source_url=link,
                                posted_at=posted_at,
                                salary_min=Decimal(str(salary_min)) if salary_min else None,
                                salary_max=Decimal(str(salary_max)) if salary_max else None,
                                salary_currency=item.get("salary_currency_code") or "USD",
                            )
                        )
                        if len(jobs) >= limit:
                            break

        logger.info("Careerjet fetched %s Java jobs", len(jobs))
        return jobs

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            pass
        try:
            dt = parsedate_to_datetime(str(value))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        except (TypeError, ValueError):
            return None
