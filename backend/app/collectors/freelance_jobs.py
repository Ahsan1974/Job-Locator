"""Freelance software gigs from Freelancer, Fiverr, Upwork, and PeoplePerHour."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from decimal import Decimal
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from app.collectors.base import JobSourceConnector, RawJob
from app.collectors.scrape_utils import http_get
from app.domain.java_filter import detect_experience_level, is_software_gig

logger = logging.getLogger(__name__)

FREELANCER_QUERIES = (
    "java developer",
    "python developer",
    "react developer",
    "software developer",
    "qa tester",
    "machine learning",
    "wordpress developer",
    "mobile app developer",
)

FIVERR_QUERIES = (
    "java developer",
    "python developer",
    "react developer",
    "wordpress",
    "qa testing",
    "machine learning",
)

UPWORK_QUERIES = (
    "java developer",
    "python developer",
    "software developer",
    "qa tester",
)

PEOPLEPERHOUR_QUERIES = (
    "java developer",
    "python developer",
    "web developer",
    "software engineer",
)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _from_freelancer_api(query: str, limit: int) -> list[RawJob]:
    url = (
        "https://www.freelancer.com/api/projects/0.1/projects/active/"
        f"?query={quote_plus(query)}&limit={limit}&full_description=true"
    )
    status, body = http_get(url)
    if status != 200 or not body.startswith("{"):
        logger.debug("Freelancer API %s HTTP %s", query, status)
        return []
    try:
        import json

        payload = json.loads(body)
    except json.JSONDecodeError:
        return []

    jobs: list[RawJob] = []
    for item in payload.get("result", {}).get("projects", []):
        title = _clean(item.get("title") or "")
        description = _clean(item.get("preview_description") or item.get("description") or "")
        if not title or not is_software_gig(title, description):
            continue
        seo = item.get("seo_url") or ""
        link = f"https://www.freelancer.com/projects/{seo}" if seo else "https://www.freelancer.com/jobs/"
        posted = None
        if item.get("time_submitted"):
            try:
                posted = datetime.fromtimestamp(int(item["time_submitted"]), tz=UTC)
            except (TypeError, ValueError, OSError):
                posted = None
        budget = item.get("budget") if isinstance(item.get("budget"), dict) else {}
        minimum = budget.get("minimum")
        maximum = budget.get("maximum")
        jobs.append(
            RawJob(
                source="freelancer",
                external_id=str(item.get("id") or seo or title)[:240],
                title=title[:180],
                description=description[:2000],
                location_raw="Remote",
                country="Remote",
                work_mode="remote",
                employment_type="freelance",
                experience_level=detect_experience_level(title, description),
                apply_url=link,
                source_url=link,
                posted_at=posted,
                salary_min=Decimal(str(minimum)) if minimum not in (None, "") else None,
                salary_max=Decimal(str(maximum)) if maximum not in (None, "") else None,
                salary_currency=(item.get("currency") or {}).get("code", "USD")
                if isinstance(item.get("currency"), dict)
                else "USD",
            )
        )
    return jobs


def _from_fiverr(query: str) -> list[RawJob]:
    url = f"https://www.fiverr.com/search/gigs?query={quote_plus(query)}"
    status, html = http_get(url)
    if status != 200:
        logger.debug("Fiverr %s HTTP %s", query, status)
        return []
    jobs: list[RawJob] = []
    seen: set[str] = set()
    for match in re.finditer(r'"gig_url":"(/[^"]+)"', html):
        path = match.group(1)
        if path in seen:
            continue
        seen.add(path)
        slug = path.rstrip("/").split("/")[-1].replace("-", " ")
        title = _clean(slug)
        if len(title) < 8 or not is_software_gig(title, query):
            continue
        seller = path.strip("/").split("/")[0].replace("-", " ")
        link = f"https://www.fiverr.com{path}"
        jobs.append(
            RawJob(
                source="fiverr",
                external_id=path[:240],
                title=title[:180].title(),
                description=f"Fiverr gig for {query}.",
                company_name=seller,
                location_raw="Remote",
                country="Remote",
                work_mode="remote",
                employment_type="freelance",
                apply_url=link,
                source_url=link,
            )
        )
        if len(jobs) >= 12:
            break
    return jobs


def _from_html_board(url: str, *, source: str, base: str) -> list[RawJob]:
    status, html = http_get(url)
    if status != 200 or len(html) < 500:
        logger.debug("%s HTTP %s %s", source, status, url)
        return []
    soup = BeautifulSoup(html, "lxml")
    jobs: list[RawJob] = []
    seen: set[str] = set()
    for link in soup.select("a[href]"):
        href = link.get("href") or ""
        title = _clean(link.get_text(" ", strip=True))
        if len(title) < 12 or len(title) > 140:
            continue
        if source == "upwork" and "/jobs/" not in href and "job" not in href.lower():
            continue
        if source == "peopleperhour" and "freelance" not in href and "/job" not in href:
            continue
        if not is_software_gig(title, ""):
            continue
        if href.startswith("/"):
            href = base.rstrip("/") + href
        if not href.startswith("http") or href in seen:
            continue
        seen.add(href)
        jobs.append(
            RawJob(
                source=source,
                external_id=href.rstrip("/").split("/")[-1][:240] or title[:80],
                title=title,
                description=title,
                location_raw="Remote",
                country="Remote",
                work_mode="remote",
                employment_type="freelance",
                apply_url=href,
                source_url=href,
            )
        )
        if len(jobs) >= 10:
            break
    return jobs


class FreelanceJobsConnector(JobSourceConnector):
    name = "freelance"

    async def fetch(self, query: str = "software developer", limit: int = 40) -> list[RawJob]:
        import asyncio

        jobs: list[RawJob] = []
        seen: set[str] = set()

        def add(batch: list[RawJob], cap: int) -> None:
            added = 0
            for job in batch:
                if len(jobs) >= limit or added >= cap:
                    return
                key = f"{job.source}:{job.external_id}"
                if key in seen:
                    continue
                seen.add(key)
                jobs.append(job)
                added += 1

        for keywords in FREELANCER_QUERIES:
            if sum(1 for j in jobs if j.source == "freelancer") >= 28:
                break
            batch = await asyncio.to_thread(_from_freelancer_api, keywords, 8)
            add(batch, 28)

        for keywords in FIVERR_QUERIES:
            if sum(1 for j in jobs if j.source == "fiverr") >= 18:
                break
            add(await asyncio.to_thread(_from_fiverr, keywords), 18)

        for keywords in UPWORK_QUERIES[:2]:
            if sum(1 for j in jobs if j.source == "upwork") >= 6:
                break
            url = f"https://www.upwork.com/nx/search/jobs/?q={quote_plus(keywords)}&sort=recency"
            add(await asyncio.to_thread(_from_html_board, url, source="upwork", base="https://www.upwork.com"), 6)

        for keywords in PEOPLEPERHOUR_QUERIES[:2]:
            if sum(1 for j in jobs if j.source == "peopleperhour") >= 6:
                break
            url = f"https://www.peopleperhour.com/freelance-jobs?keyword={quote_plus(keywords)}"
            add(
                await asyncio.to_thread(
                    _from_html_board,
                    url,
                    source="peopleperhour",
                    base="https://www.peopleperhour.com",
                ),
                6,
            )

        logger.info("Freelance boards fetched %s software gigs", len(jobs))
        return jobs[:limit]
