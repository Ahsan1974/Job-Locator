"""Additional job board scrapers — Talent.com, NaukriGulf (UAE/visa), visa-focused searches."""

from __future__ import annotations

import logging
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from app.collectors.base import JobSourceConnector, RawJob
from app.collectors.scrape_utils import http_get, parse_posted_date
from app.domain.country import normalize_country
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_from_aggregator,
    normalize_work_mode,
)

logger = logging.getLogger(__name__)

TALENT_SEARCHES = (
    ("java developer", "United States"),
    ("java developer", "Germany"),
    ("java developer", "United Kingdom"),
    ("java developer", "Pakistan"),
    ("java developer", "United Arab Emirates"),
    ("java spring boot", "Remote"),
    ("java developer visa sponsorship", "United States"),
    ("java developer visa sponsorship", "Canada"),
    ("java developer visa sponsorship", "Germany"),
    ("java developer visa sponsorship", "United Arab Emirates"),
)

NAUKRIGULF_SEARCHES = (
    "java developer",
    "java spring boot",
    "java backend",
)


def _parse_talent_html(html: str, country: str) -> list[RawJob]:
    jobs: list[RawJob] = []
    seen: set[str] = set()
    soup = BeautifulSoup(html, "lxml")

    for card in soup.select("article, div.card-job, div.job-card, li.job-list-item, div[data-job-id]"):
        link = card.select_one('a[href*="/job/"], a[href*="viewjob"]')
        if not link:
            continue
        href = link.get("href", "")
        if href and not href.startswith("http"):
            href = f"https://www.talent.com{href}"
        title_el = card.select_one("h2, h3, .job-title, [data-testid='job-title']") or link
        title = title_el.get_text(strip=True)
        if not title:
            continue
        company_el = card.select_one(".company, .company-name, [data-testid='company-name']")
        loc_el = card.select_one(".location, .job-location, [data-testid='job-location']")
        date_el = card.select_one("time, .date, .job-date")
        description = card.get_text(" ", strip=True)[:700]
        if not is_java_related_from_aggregator(title, description):
            continue
        ext_id = href.rstrip("/").split("/")[-1] if href else title
        if ext_id in seen:
            continue
        seen.add(ext_id)
        location = loc_el.get_text(strip=True) if loc_el else country
        blob = f"{title} {description} {location}"
        visa_query = "visa" in title.lower() or "visa" in description.lower()
        jobs.append(
            RawJob(
                source="talent",
                external_id=ext_id,
                title=title,
                description=description,
                company_name=company_el.get_text(strip=True) if company_el else None,
                location_raw=location,
                city=location.split(",")[0].strip() if location and "," in location else None,
                country=normalize_country(country) if country != "Remote" else "Remote",
                work_mode=normalize_work_mode(blob, location=location),
                experience_level=detect_experience_level(title, description),
                visa_sponsorship=detect_visa_sponsorship(blob) or visa_query,
                apply_url=href,
                source_url=href,
                posted_at=parse_posted_date(
                    date_el.get("datetime") if date_el and date_el.get("datetime") else (
                        date_el.get_text(strip=True) if date_el else None
                    )
                ),
            )
        )
    return jobs


def _parse_naukrigulf_html(html: str) -> list[RawJob]:
    jobs: list[RawJob] = []
    seen: set[str] = set()
    soup = BeautifulSoup(html, "lxml")

    for card in soup.select("article, div.job, li.job, div.srp-job"):
        link = card.select_one('a[href*="/job/"], a[href*="/jobs/"]')
        if not link:
            continue
        href = link.get("href", "")
        if not href.startswith("http"):
            href = f"https://www.naukrigulf.com{href}"
        title = (card.select_one("h2, h3, .job-title") or link).get_text(strip=True)
        if not title:
            continue
        company_el = card.select_one(".company, .employer")
        loc_el = card.select_one(".location, .city")
        description = card.get_text(" ", strip=True)[:700]
        if not is_java_related_from_aggregator(title, description):
            continue
        ext_id = re.sub(r"[^a-zA-Z0-9_-]", "", href.split("/")[-1]) or title
        if ext_id in seen:
            continue
        seen.add(ext_id)
        location = loc_el.get_text(strip=True) if loc_el else "UAE"
        blob = f"{title} {description} {location}"
        jobs.append(
            RawJob(
                source="naukrigulf",
                external_id=ext_id,
                title=title,
                description=description,
                company_name=company_el.get_text(strip=True) if company_el else None,
                location_raw=location,
                country=normalize_country(location.split(",")[-1] if "," in location else "United Arab Emirates"),
                work_mode=normalize_work_mode(blob, location=location),
                experience_level=detect_experience_level(title, description),
                visa_sponsorship=True,
                apply_url=href,
                source_url=href,
                posted_at=None,
            )
        )
    return jobs


class ExtraBoardsConnector(JobSourceConnector):
    """Talent.com + NaukriGulf for more global and visa-friendly listings."""

    name = "extra_boards"

    async def fetch(self, query: str = "java developer", limit: int = 80) -> list[RawJob]:
        jobs: list[RawJob] = []
        seen: set[str] = set()

        for keywords, country in TALENT_SEARCHES:
            if len(jobs) >= limit:
                break
            url = (
                f"https://www.talent.com/jobs?"
                f"k={quote_plus(keywords)}&l={quote_plus(country)}"
            )
            status, html = http_get(url)
            if status != 200:
                logger.debug("Talent.com %s/%s HTTP %s", country, keywords, status)
                continue
            for job in _parse_talent_html(html, country):
                if job.external_id in seen:
                    continue
                seen.add(job.external_id)
                jobs.append(job)
                if len(jobs) >= limit:
                    break

        for kw in NAUKRIGULF_SEARCHES:
            if len(jobs) >= limit:
                break
            url = f"https://www.naukrigulf.com/java-developer-jobs-in-uae?k={quote_plus(kw)}"
            status, html = http_get(url)
            if status != 200:
                url = f"https://www.naukrigulf.com/search-jobs?Keywords={quote_plus(kw)}&Location=UAE"
                status, html = http_get(url)
            if status == 200:
                for job in _parse_naukrigulf_html(html):
                    key = f"{job.source}-{job.external_id}"
                    if key in seen:
                        continue
                    seen.add(key)
                    jobs.append(job)
                    if len(jobs) >= limit:
                        break

        logger.info("Extra boards fetched %s Java jobs", len(jobs))
        return jobs[:limit]
