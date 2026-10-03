"""Pakistan-focused job sources — Indeed PK, Rozee.pk, Mustakbil, Jooble PK."""

import json
import logging
import re
from datetime import UTC, datetime
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from app.collectors.base import JobSourceConnector, RawJob
from app.collectors.scrape_utils import http_get, parse_posted_date
from app.core.config import get_settings
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_from_aggregator,
)

logger = logging.getLogger(__name__)

PK_CITIES = (
    "Lahore",
    "Karachi",
    "Islamabad",
    "Rawalpindi",
    "Faisalabad",
    "Multan",
    "Peshawar",
    "Hyderabad",
    "Sialkot",
    "Gujranwala",
    "Quetta",
    "Bahawalpur",
    "Abbottabad",
)

INDIA_LOCATION_MARKERS = (
    "india",
    "telangana",
    "maharashtra",
    "karnataka",
    "tamil nadu",
    "bengaluru",
    "bangalore",
    "mumbai",
    "delhi",
    "pune",
    "chennai",
    "kolkata",
    "gurgaon",
    "noida",
    "andhra pradesh",
    "kerala",
)

PK_LOCATION_MARKERS = (
    "pakistan",
    "punjab",
    "sindh",
    "kpk",
    "khyber",
    "balochistan",
    "azad kashmir",
    "gilgit",
    *PK_CITIES,
)

SEARCH_KEYWORDS = (
    "java developer",
    "spring boot developer",
    "python developer",
    "software engineer",
    "qa engineer",
    "backend developer java",
)


def _is_india_location(text: str | None) -> bool:
    if not text:
        return False
    t = text.lower()
    return any(m in t for m in INDIA_LOCATION_MARKERS)


def _is_pakistan_location(text: str | None) -> bool:
    if not text:
        return False
    t = text.lower()
    if _is_india_location(t):
        return False
    if "hyderabad" in t:
        return "pakistan" in t or "sindh" in t
    return any(m in t for m in PK_LOCATION_MARKERS)


def _pk_city_from_location(location: str | None, fallback: str | None = None) -> str | None:
    if not location:
        return fallback
    if _is_india_location(location):
        return None
    loc_l = location.lower()
    for city in PK_CITIES:
        if city.lower() in loc_l:
            return city
    if fallback and fallback.lower() in loc_l:
        return fallback
    if "," in location:
        return location.split(",")[0].strip()
    return fallback


def _is_pk_java_job(title: str, description: str | None = None) -> bool:
    if is_java_related_from_aggregator(title, description):
        return True
    title_l = (title or "").lower()
    desc_l = (description or "").lower()
    if "javascript" in title_l and "java" not in title_l:
        return False
    if re.search(r"\bjava\b", title_l):
        return True
    if re.search(r"\bspring\b", title_l) and re.search(r"\b(developer|engineer)\b", title_l):
        return True
    if re.search(r"\b(backend|software engineer|full stack)\b", title_l) and re.search(
        r"\bjava\b", desc_l[:1500]
    ):
        return True
    return False


def _parse_indeed_html(html: str, source: str, search_city: str | None = None) -> list[RawJob]:
    jobs: list[RawJob] = []
    seen: set[str] = set()

    for match in re.finditer(r'"jobkey"\s*:\s*"([a-f0-9]+)"', html):
        jk = match.group(1)
        if jk in seen:
            continue
        chunk = html[match.start() : match.start() + 3000]
        title_m = re.search(r'"title"\s*:\s*"([^"]+)"', chunk)
        company_m = re.search(r'"company"\s*:\s*"([^"]+)"', chunk)
        loc_m = re.search(r'"formattedLocation"\s*:\s*"([^"]+)"', chunk)
        snippet_m = re.search(r'"snippet"\s*:\s*"([^"]*)"', chunk)
        date_m = re.search(r'"pubDate"\s*:\s*(\d+)', chunk)
        if not title_m:
            continue
        title = title_m.group(1).encode().decode("unicode_escape")
        description = (snippet_m.group(1) if snippet_m else "").encode().decode("unicode_escape")
        location = (loc_m.group(1) if loc_m else "").encode().decode("unicode_escape")
        if _is_india_location(location):
            continue
        if not _is_pakistan_location(location) and search_city:
            location = f"{search_city}, Pakistan"
        if not _is_pk_java_job(title, description):
            continue
        seen.add(jk)
        company = company_m.group(1).encode().decode("unicode_escape") if company_m else None
        apply_url = f"https://pk.indeed.com/viewjob?jk={jk}"
        blob = f"{title} {description} {location}"
        posted_at = None
        if date_m:
            try:
                posted_at = datetime.fromtimestamp(int(date_m.group(1)) / 1000, tz=UTC)
            except (ValueError, OSError):
                posted_at = None
        jobs.append(
            RawJob(
                source=source,
                external_id=f"indeed-{jk}",
                title=title,
                description=description,
                company_name=company,
                location_raw=location or "Pakistan",
                city=_pk_city_from_location(location, search_city),
                country="Pakistan",
                work_mode=detect_work_mode(blob),
                experience_level=detect_experience_level(title, description),
                visa_sponsorship=detect_visa_sponsorship(blob),
                apply_url=apply_url,
                source_url=apply_url,
                posted_at=posted_at,
            )
        )

    if jobs:
        return jobs

    soup = BeautifulSoup(html, "lxml")
    for card in soup.select("div.job_seen_beacon, div.slider_item, td.resultContent"):
        link = card.select_one('a[href*="jk="], a[data-jk], h2.jobTitle a')
        if not link:
            continue
        title = link.get_text(strip=True)
        href = link.get("href", "")
        jk = link.get("data-jk") or ""
        if not jk and "jk=" in href:
            jk = href.split("jk=")[-1].split("&")[0]
        if not jk or jk in seen:
            continue
        company_el = card.select_one('[data-testid="company-name"], .companyName')
        loc_el = card.select_one('[data-testid="text-location"], .companyLocation')
        date_el = card.select_one("span.date, span.datePosted")
        description = card.get_text(" ", strip=True)[:500]
        location = loc_el.get_text(strip=True) if loc_el else ""
        if _is_india_location(location):
            continue
        if not _is_pakistan_location(location) and search_city:
            location = f"{search_city}, Pakistan"
        if not _is_pk_java_job(title, description):
            continue
        seen.add(jk)
        company = company_el.get_text(strip=True) if company_el else None
        apply_url = f"https://pk.indeed.com/viewjob?jk={jk}"
        blob = f"{title} {description} {location}"
        jobs.append(
            RawJob(
                source=source,
                external_id=f"indeed-{jk}",
                title=title,
                description=description,
                company_name=company,
                location_raw=location or "Pakistan",
                city=_pk_city_from_location(location, search_city),
                country="Pakistan",
                work_mode=detect_work_mode(blob),
                experience_level=detect_experience_level(title, description),
                visa_sponsorship=detect_visa_sponsorship(blob),
                apply_url=apply_url,
                source_url=apply_url,
                posted_at=parse_posted_date(date_el.get_text(strip=True) if date_el else None),
            )
        )
    return jobs


def _parse_rozee_html(html: str, search_city: str | None = None) -> list[RawJob]:
    jobs: list[RawJob] = []
    seen: set[str] = set()
    soup = BeautifulSoup(html, "lxml")

    for card in soup.select("div.job, div.srp-job-listing, li.job-listing, article, div.job-list"):
        link = card.select_one('a[href*="/job/"]')
        if not link:
            continue
        href = link.get("href", "")
        if not href.startswith("http"):
            href = f"https://www.rozee.pk{href}"
        title_el = card.select_one("h3, h2, .job-title, .jtitle") or link
        title = title_el.get_text(strip=True)
        company_el = card.select_one(".company-name, .jcompany, .employer")
        loc_el = card.select_one(".location, .jlocation, .city")
        description = card.get_text(" ", strip=True)[:800]
        if not _is_pk_java_job(title, description):
            continue
        ext_id = href.rstrip("/").split("/")[-1]
        if ext_id in seen:
            continue
        seen.add(ext_id)
        location = loc_el.get_text(strip=True) if loc_el else (f"{search_city}, Pakistan" if search_city else "Pakistan")
        if _is_india_location(location):
            continue
        company = company_el.get_text(strip=True) if company_el else None
        blob = f"{title} {description} {location}"
        jobs.append(
            RawJob(
                source="rozee",
                external_id=ext_id,
                title=title,
                description=description,
                company_name=company,
                location_raw=location,
                city=_pk_city_from_location(location, search_city),
                country="Pakistan",
                work_mode=detect_work_mode(blob),
                experience_level=detect_experience_level(title, description),
                visa_sponsorship=detect_visa_sponsorship(blob),
                apply_url=href,
                source_url=href,
                posted_at=None,
            )
        )
    return jobs


def _parse_mustakbil_html(html: str, search_city: str | None = None) -> list[RawJob]:
    jobs: list[RawJob] = []
    seen: set[str] = set()
    soup = BeautifulSoup(html, "lxml")

    for card in soup.select("div.job-listing, div.job-card, article, .search-result-item, tr"):
        link = card.select_one('a[href*="/job/"], a[href*="/jobs/"]')
        if not link:
            continue
        href = link.get("href", "")
        if not href.startswith("http"):
            href = f"https://www.mustakbil.com{href}"
        title = (card.select_one("h2, h3, .job-title, a") or link).get_text(strip=True)
        if not title or len(title) < 4:
            continue
        company_el = card.select_one(".company, .company-name, .employer")
        loc_el = card.select_one(".location, .city, .job-location")
        description = card.get_text(" ", strip=True)[:600]
        if not _is_pk_java_job(title, description):
            continue
        ext_id = href.rstrip("/").split("/")[-1] or href
        if ext_id in seen:
            continue
        seen.add(ext_id)
        location = loc_el.get_text(strip=True) if loc_el else (f"{search_city}, Pakistan" if search_city else "Pakistan")
        if _is_india_location(location):
            continue
        blob = f"{title} {description} {location}"
        jobs.append(
            RawJob(
                source="mustakbil",
                external_id=ext_id,
                title=title,
                description=description,
                company_name=company_el.get_text(strip=True) if company_el else None,
                location_raw=location,
                city=_pk_city_from_location(location, search_city),
                country="Pakistan",
                work_mode=detect_work_mode(blob),
                experience_level=detect_experience_level(title, description),
                visa_sponsorship=detect_visa_sponsorship(blob),
                apply_url=href,
                source_url=href,
                posted_at=None,
            )
        )
    return jobs


class PakistanJobsConnector(JobSourceConnector):
    """Indeed PK + Rozee.pk + Mustakbil + Jooble Pakistan city searches."""

    name = "pakistan"

    async def fetch(self, query: str = "java developer", limit: int = 80) -> list[RawJob]:
        settings = get_settings()
        if not settings.enable_pakistan_scraping:
            return []

        jobs: list[RawJob] = []
        seen: set[str] = set()

        def add_batch(batch: list[RawJob]) -> None:
            for job in batch:
                if job.external_id in seen:
                    continue
                if job.location_raw and _is_india_location(job.location_raw):
                    continue
                seen.add(job.external_id)
                job.country = "Pakistan"
                if not job.city and job.location_raw:
                    job.city = _pk_city_from_location(job.location_raw)
                jobs.append(job)
                if len(jobs) >= limit:
                    return

        # Nationwide Indeed PK
        for kw in SEARCH_KEYWORDS[:3]:
            if len(jobs) >= limit:
                break
            for start in (0,):
                url = f"https://pk.indeed.com/jobs?q={quote_plus(kw)}&l=Pakistan&start={start}"
                status, html = http_get(url)
                if status != 200:
                    break
                batch = _parse_indeed_html(html, "indeed_pk")
                if not batch:
                    break
                add_batch(batch)

        # Indeed per city
        for city in PK_CITIES:
            if len(jobs) >= limit:
                break
            for kw in SEARCH_KEYWORDS[:4]:
                if len(jobs) >= limit:
                    break
                for start in (0,):
                    url = (
                        f"https://pk.indeed.com/jobs?q={quote_plus(kw)}"
                        f"&l={quote_plus(city + ', Pakistan')}&start={start}"
                    )
                    status, html = http_get(url)
                    if status != 200:
                        logger.debug("Indeed PK %s/%s -> HTTP %s", city, kw, status)
                        break
                    batch = _parse_indeed_html(html, "indeed_pk", search_city=city)
                    if not batch:
                        break
                    add_batch(batch)

        # Rozee.pk — all cities
        for city in PK_CITIES:
            if len(jobs) >= limit:
                break
            for kw in ("Java Developer", "Spring Boot", "Software Engineer Java"):
                slug = quote_plus(kw)
                city_slug = quote_plus(city)
                url = f"https://www.rozee.pk/job/jsearch/q/{slug}/loc/{city_slug}"
                status, html = http_get(url)
                if status == 200:
                    add_batch(_parse_rozee_html(html, search_city=city))

        # Mustakbil.com
        for city in PK_CITIES:
            if len(jobs) >= limit:
                break
            for kw in ("java developer", "spring boot"):
                url = (
                    f"https://www.mustakbil.com/jobs/search?"
                    f"keywords={quote_plus(kw)}&location={quote_plus(city)}"
                )
                status, html = http_get(url)
                if status == 200:
                    add_batch(_parse_mustakbil_html(html, search_city=city))

        # Jooble Pakistan cities (API)
        if settings.jooble_api_key and len(jobs) < limit:
            import httpx

            url = f"https://jooble.org/api/{settings.jooble_api_key}"
            headers = {"Content-Type": "application/json", "User-Agent": "JavaCareerAI/1.0"}
            async with httpx.AsyncClient(timeout=45.0, headers=headers) as client:
                for city in PK_CITIES:
                    if len(jobs) >= limit:
                        break
                    for kw in SEARCH_KEYWORDS:
                        if len(jobs) >= limit:
                            break
                        for page in range(1, 4):
                            try:
                                response = await client.post(
                                    url,
                                    json={
                                        "keywords": kw,
                                        "location": f"{city}, Pakistan",
                                        "page": str(page),
                                    },
                                )
                                response.raise_for_status()
                                payload = response.json()
                            except Exception:
                                break
                            batch_items = payload.get("jobs", [])
                            if not batch_items:
                                break
                            for item in batch_items:
                                title = item.get("title") or ""
                                snippet = item.get("snippet") or ""
                                loc = item.get("location") or f"{city}, Pakistan"
                                if _is_india_location(loc):
                                    continue
                                if not _is_pakistan_location(loc) and city.lower() not in loc.lower():
                                    continue
                                if not _is_pk_java_job(title, snippet):
                                    continue
                                ext_id = str(item.get("id") or item.get("link") or title)
                                if ext_id in seen:
                                    continue
                                seen.add(ext_id)
                                link = item.get("link") or ""
                                blob = f"{title} {snippet} {loc}"
                                jobs.append(
                                    RawJob(
                                        source="jooble_pk",
                                        external_id=ext_id,
                                        title=title,
                                        description=snippet,
                                        company_name=item.get("company"),
                                        location_raw=loc,
                                        city=_pk_city_from_location(loc, city),
                                        country="Pakistan",
                                        work_mode=detect_work_mode(blob),
                                        experience_level=detect_experience_level(title, snippet),
                                        visa_sponsorship=detect_visa_sponsorship(blob),
                                        apply_url=link,
                                        source_url=link,
                                        posted_at=parse_posted_date(item.get("updated")),
                                    )
                                )
                                if len(jobs) >= limit:
                                    break

        logger.info("Pakistan connector fetched %s Java jobs", len(jobs))
        return jobs[:limit]
