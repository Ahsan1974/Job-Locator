"""LinkedIn public guest job search — Java roles worldwide (onsite + remote)."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.collectors.base import JobSourceConnector, RawJob
from app.core.config import get_settings
from app.domain.country import normalize_country
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    is_java_related_from_aggregator,
    normalize_work_mode,
)

logger = logging.getLogger(__name__)

SEARCH_API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
DETAIL_API = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

JAVA_KEYWORDS = (
    "java developer",
    "python developer",
    "ai engineer",
    "qa engineer",
    "technical project manager",
    "machine learning engineer",
)

# (LinkedIn location query, normalized country label)
LINKEDIN_REGIONS: tuple[tuple[str, str], ...] = (
    ("United States", "United States"),
    ("United Kingdom", "United Kingdom"),
    ("Germany", "Germany"),
    ("Pakistan", "Pakistan"),
    ("United Arab Emirates", "United Arab Emirates"),
    ("Remote", "Remote"),
)

# f_WT: 1 = onsite, 2 = remote, 3 = hybrid
WORK_TYPE_FILTERS: tuple[tuple[str | None, str | None], ...] = (
    (None, None),
)


def _http_get(url: str, params: dict | None = None) -> tuple[int, str]:
    try:
        from curl_cffi import requests as cffi_requests

        response = cffi_requests.get(url, params=params, impersonate="chrome120", timeout=40)
        return response.status_code, response.text
    except Exception as exc:
        logger.debug("curl_cffi GET failed %s: %s", url, exc)

    try:
        import httpx

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = httpx.get(url, params=params, headers=headers, timeout=40, follow_redirects=True)
        return response.status_code, response.text
    except Exception as exc:
        logger.debug("httpx GET failed %s: %s", url, exc)
        return 0, ""


def _parse_cards(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    cards: list[dict] = []
    for card in soup.select("div.base-search-card"):
        urn = card.get("data-entity-urn") or ""
        job_id = urn.split(":")[-1] if ":" in urn else ""
        if not job_id:
            continue

        title_el = card.select_one("h3.base-search-card__title")
        company_el = card.select_one("h4.base-search-card__subtitle")
        location_el = card.select_one("span.job-search-card__location")
        link_el = card.select_one("a.base-card__full-link")
        logo_el = card.select_one("img[data-delayed-url], img.artdeco-entity-image")
        time_el = card.select_one("time.job-search-card__listdate")

        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            continue

        posted_at = None
        if time_el and time_el.get("datetime"):
            try:
                posted_at = datetime.strptime(time_el["datetime"], "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError:
                posted_at = None

        href = link_el.get("href") if link_el else None
        if href and href.startswith("/"):
            href = urljoin("https://www.linkedin.com", href)

        cards.append(
            {
                "job_id": job_id,
                "title": title,
                "company": company_el.get_text(strip=True) if company_el else None,
                "location": location_el.get_text(strip=True) if location_el else None,
                "apply_url": href,
                "logo": logo_el.get("data-delayed-url") or logo_el.get("src") if logo_el else None,
                "posted_at": posted_at,
            }
        )
    return cards


def _fetch_job_description(job_id: str) -> str | None:
    status, html = _http_get(DETAIL_API.format(job_id=job_id))
    if status != 200 or not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    markup = soup.select_one("div.show-more-less-html__markup, div.description__text")
    if markup:
        return markup.get_text("\n", strip=True)[:8000]
    return None


def _infer_city(location: str | None) -> str | None:
    if not location:
        return None
    parts = [p.strip() for p in location.split(",")]
    return parts[0] if parts else None


def _infer_country(location: str | None, region_country: str) -> str | None:
    if region_country == "Remote":
        if location and "remote" in location.lower():
            return "Remote"
        return normalize_country(location) or "Remote"
    if location:
        parts = [p.strip() for p in location.split(",") if p.strip()]
        if len(parts) >= 2:
            tail_norm = normalize_country(parts[-1])
            if tail_norm and len(tail_norm) > 3:
                return tail_norm
    return normalize_country(region_country)


class LinkedInJobsConnector(JobSourceConnector):
    name = "linkedin"

    async def fetch(self, query: str = "java developer", limit: int = 100) -> list[RawJob]:
        settings = get_settings()
        if not settings.enable_linkedin_scraping:
            logger.info("LinkedIn scraping disabled — set ENABLE_LINKEDIN_SCRAPING=true")
            return []

        jobs: list[RawJob] = []
        seen: set[str] = set()
        pending_details: list[dict] = []

        per_keyword = max(6, limit // len(JAVA_KEYWORDS))
        keyword_counts: dict[str, int] = {}

        for keywords in JAVA_KEYWORDS:
            if len(jobs) + len(pending_details) >= limit:
                break
            for location, region_country in LINKEDIN_REGIONS:
                if (
                    len(jobs) + len(pending_details) >= limit
                    or keyword_counts.get(keywords, 0) >= per_keyword
                ):
                    break
                for work_type_code, mode_hint in WORK_TYPE_FILTERS:
                    if region_country == "Remote" and work_type_code == "1":
                        continue
                    if len(jobs) + len(pending_details) >= limit:
                        break
                    for start in (0,):
                        if len(jobs) + len(pending_details) >= limit:
                            break
                        params: dict[str, str | int] = {
                            "keywords": keywords,
                            "location": location,
                            "start": start,
                        }
                        if work_type_code:
                            params["f_WT"] = work_type_code

                        status, html = await asyncio.to_thread(_http_get, SEARCH_API, params)
                        if status != 200 or not html.strip():
                            break

                        batch = _parse_cards(html)
                        if not batch:
                            break

                        for item in batch:
                            ext_id = item["job_id"]
                            if ext_id in seen:
                                continue
                            seen.add(ext_id)

                            title = item["title"]
                            location_raw = item.get("location")
                            blob = f"{title} {location_raw or ''}"
                            if not is_java_related_from_aggregator(title, ""):
                                pending_details.append({**item, "region_country": region_country, "mode_hint": mode_hint})
                                continue

                            work_mode = normalize_work_mode(
                                blob, fallback=mode_hint, location=location_raw
                            )
                            if region_country == "Remote" and work_mode is None:
                                work_mode = "remote"

                            country = _infer_country(location_raw, region_country)
                            jobs.append(
                                RawJob(
                                    source=self.name,
                                    external_id=ext_id,
                                    title=title,
                                    description=None,
                                    company_name=item.get("company"),
                                    company_logo=item.get("logo"),
                                    location_raw=location_raw,
                                    city=_infer_city(location_raw),
                                    country=country,
                                    work_mode=work_mode,
                                    experience_level=detect_experience_level(title, ""),
                                    visa_sponsorship=detect_visa_sponsorship(blob),
                                    apply_url=item.get("apply_url"),
                                    source_url=item.get("apply_url"),
                                    posted_at=item.get("posted_at"),
                                )
                            )
                            keyword_counts[keywords] = keyword_counts.get(keywords, 0) + 1
                            if len(jobs) >= limit or keyword_counts[keywords] >= per_keyword:
                                break

        logger.info("LinkedIn fetched %s jobs", len(jobs))
        return jobs

    async def _enrich_with_details(self, candidates: list[dict], max_jobs: int) -> list[RawJob]:
        results: list[RawJob] = []
        sem = asyncio.Semaphore(4)

        async def process(item: dict) -> RawJob | None:
            async with sem:
                description = await asyncio.to_thread(_fetch_job_description, item["job_id"])
                await asyncio.sleep(0.25)
            title = item["title"]
            if not is_java_related_from_aggregator(title, description):
                return None
            location_raw = item.get("location")
            region_country = item.get("region_country", "")
            mode_hint = item.get("mode_hint")
            blob = f"{title} {description or ''} {location_raw or ''}"
            work_mode = normalize_work_mode(blob, fallback=mode_hint, location=location_raw)
            if region_country == "Remote" and work_mode is None:
                work_mode = "remote"
            return RawJob(
                source=self.name,
                external_id=item["job_id"],
                title=title,
                description=description,
                company_name=item.get("company"),
                company_logo=item.get("logo"),
                location_raw=location_raw,
                city=_infer_city(location_raw),
                country=_infer_country(location_raw, region_country),
                work_mode=work_mode,
                experience_level=detect_experience_level(title, description or ""),
                visa_sponsorship=detect_visa_sponsorship(blob),
                apply_url=item.get("apply_url"),
                source_url=item.get("apply_url"),
                posted_at=item.get("posted_at"),
            )

        tasks = [process(item) for item in candidates]
        for coro in asyncio.as_completed(tasks):
            if len(results) >= max_jobs:
                break
            raw = await coro
            if raw:
                results.append(raw)
        return results
