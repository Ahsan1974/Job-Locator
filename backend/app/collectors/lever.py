"""Lever public Postings API."""

from datetime import datetime

import httpx

from app.collectors.base import JobSourceConnector, RawJob
from app.domain.country import normalize_country
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_from_aggregator,
)

LEVER_COMPANIES = (
    "netflix", "spotify", "palantir", "atlassian", "canva", "rippling",
    "scale", "anduril", "cloudflare", "doordash", "flexport", "gusto",
    "hashicorp", "loom", "mercury", "notion", "ramp", "retool", "samsara",
    "segment", "toast", "webflow", "zapier", "benchling", "carta",
)


class LeverConnector(JobSourceConnector):
    name = "lever"

    async def fetch(self, query: str = "java", limit: int = 50) -> list[RawJob]:
        jobs: list[RawJob] = []
        seen: set[str] = set()
        headers = {"User-Agent": "JavaCareerAI/1.0"}

        async with httpx.AsyncClient(timeout=45.0, headers=headers) as client:
            for company in LEVER_COMPANIES:
                if len(jobs) >= limit:
                    break
                url = f"https://api.lever.co/v0/postings/{company}"
                try:
                    response = await client.get(url, params={"mode": "json"})
                    if response.status_code == 404:
                        continue
                    response.raise_for_status()
                    postings = response.json()
                except Exception:
                    continue

                if not isinstance(postings, list):
                    continue

                for item in postings:
                    title = item.get("text") or ""
                    description = (item.get("descriptionPlain") or item.get("description") or "")[:5000]
                    if not is_java_related_from_aggregator(title, description):
                        continue
                    ext_id = str(item.get("id") or f"{company}-{title}")
                    if ext_id in seen:
                        continue
                    seen.add(ext_id)

                    loc = item.get("categories", {}).get("location") if isinstance(item.get("categories"), dict) else None
                    apply_url = item.get("hostedUrl") or item.get("applyUrl")
                    posted_at = None
                    if item.get("createdAt"):
                        try:
                            posted_at = datetime.fromtimestamp(item["createdAt"] / 1000)
                        except (TypeError, ValueError, OSError):
                            posted_at = None

                    blob = f"{title} {description} {loc or ''}"
                    jobs.append(
                        RawJob(
                            source=self.name,
                            external_id=ext_id,
                            title=title,
                            description=description,
                            company_name=company.replace("-", " ").title(),
                            location_raw=str(loc) if loc else None,
                            country=normalize_country(str(loc).split(",")[-1].strip() if loc else None),
                            work_mode=detect_work_mode(blob),
                            employment_type=(item.get("categories", {}) or {}).get("commitment", "").replace("-", "_") or None,
                            experience_level=detect_experience_level(title, description),
                            visa_sponsorship=detect_visa_sponsorship(blob),
                            apply_url=apply_url,
                            source_url=apply_url,
                            posted_at=posted_at,
                        )
                    )
                    if len(jobs) >= limit:
                        break
        return jobs
