"""We Work Remotely RSS — programming jobs (public feed)."""

import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from app.collectors.base import JobSourceConnector, RawJob
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_job,
)


class WeWorkRemotelyConnector(JobSourceConnector):
    name = "weworkremotely"
    FEED_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"

    async def fetch(self, query: str = "java", limit: int = 50) -> list[RawJob]:
        headers = {"User-Agent": "JavaCareerAI/1.0"}
        async with httpx.AsyncClient(timeout=45.0, headers=headers) as client:
            response = await client.get(self.FEED_URL)
            response.raise_for_status()
            text = response.text

        feed = feedparser.parse(text)
        jobs: list[RawJob] = []
        for entry in feed.entries:
            title = entry.get("title") or ""
            description = entry.get("summary") or entry.get("description") or ""
            if not is_java_related_job(title, description):
                continue
            link = entry.get("link")
            company = None
            if ":" in title:
                parts = title.split(":", 1)
                company, title = parts[0].strip(), parts[1].strip()
            posted_at = None
            if entry.get("published"):
                try:
                    posted_at = parsedate_to_datetime(entry["published"])
                    if posted_at.tzinfo is None:
                        posted_at = posted_at.replace(tzinfo=UTC)
                except Exception:
                    posted_at = None
            blob = f"{title} {description}"
            jobs.append(
                RawJob(
                    source=self.name,
                    external_id=str(entry.get("id") or link),
                    title=title,
                    description=description,
                    company_name=company,
                    country="Remote",
                    work_mode=detect_work_mode(blob) or "remote",
                    experience_level=detect_experience_level(title, description),
                    visa_sponsorship=detect_visa_sponsorship(blob),
                    apply_url=link,
                    source_url=link,
                    posted_at=posted_at,
                )
            )
            if len(jobs) >= limit:
                break
        return jobs
