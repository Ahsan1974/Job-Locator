"""Multiple RSS job feeds from remote-first boards."""

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from app.collectors.base import JobSourceConnector, RawJob
from app.domain.country import normalize_country
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_job,
)

RSS_FEEDS: tuple[tuple[str, str], ...] = (
    ("weworkremotely", "https://weworkremotely.com/categories/remote-programming-jobs.rss"),
    ("weworkremotely-devops", "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"),
    ("remoteco", "https://remote.co/job-category/developer/feed/"),
    ("authenticjobs", "https://authenticjobs.com/rss/custom.php?type=rss&terms=java"),
)


class RssFeedsConnector(JobSourceConnector):
    name = "rss_feeds"

    async def fetch(self, query: str = "java", limit: int = 50) -> list[RawJob]:
        jobs: list[RawJob] = []
        seen: set[str] = set()
        per_feed = max(10, limit // len(RSS_FEEDS))
        headers = {"User-Agent": "JavaCareerAI/1.0"}

        async with httpx.AsyncClient(timeout=45.0, headers=headers, follow_redirects=True) as client:
            for source_key, feed_url in RSS_FEEDS:
                if len(jobs) >= limit:
                    break
                try:
                    response = await client.get(feed_url)
                    response.raise_for_status()
                    feed = feedparser.parse(response.text)
                except Exception:
                    continue

                for entry in feed.entries:
                    title = entry.get("title") or ""
                    description = entry.get("summary") or entry.get("description") or ""
                    if not is_java_related_job(title, description):
                        continue

                    link = entry.get("link")
                    ext_id = str(entry.get("id") or link or title)
                    if ext_id in seen:
                        continue
                    seen.add(ext_id)

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
                            source=source_key,
                            external_id=ext_id,
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
                    if len(jobs) >= per_feed:
                        break
        return jobs
