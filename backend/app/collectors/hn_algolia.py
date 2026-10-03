"""Hacker News Jobs via Algolia public API."""

from datetime import UTC, datetime

import httpx

from app.collectors.base import JobSourceConnector, RawJob
from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_from_aggregator,
)

SEARCH_URL = "https://hn.algolia.com/api/v1/search"


class HnAlgoliaConnector(JobSourceConnector):
    name = "hn_algolia"

    async def fetch(self, query: str = "java", limit: int = 50) -> list[RawJob]:
        jobs: list[RawJob] = []
        seen: set[str] = set()
        headers = {"User-Agent": "JavaCareerAI/1.0"}

        async with httpx.AsyncClient(timeout=45.0, headers=headers) as client:
            for search_q in ("java developer", "spring boot", "java backend"):
                if len(jobs) >= limit:
                    break
                try:
                    response = await client.get(
                        SEARCH_URL,
                        params={"query": search_q, "tags": "job", "hitsPerPage": 50},
                    )
                    response.raise_for_status()
                    hits = response.json().get("hits", [])
                except Exception:
                    continue

                for item in hits:
                    title = item.get("title") or ""
                    story = item.get("story_text") or item.get("comment_text") or ""
                    if not is_java_related_from_aggregator(title, story):
                        continue
                    ext_id = str(item.get("objectID") or item.get("url") or title)
                    if ext_id in seen:
                        continue
                    seen.add(ext_id)

                    url = item.get("url") or f"https://news.ycombinator.com/item?id={item.get('objectID')}"
                    posted_at = None
                    if item.get("created_at_i"):
                        posted_at = datetime.fromtimestamp(item["created_at_i"], tz=UTC)

                    blob = f"{title} {story}"
                    jobs.append(
                        RawJob(
                            source=self.name,
                            external_id=ext_id,
                            title=title,
                            description=story[:4000] if story else title,
                            company_name=self._company_from_title(title),
                            country="Remote",
                            work_mode=detect_work_mode(blob) or "remote",
                            experience_level=detect_experience_level(title, story),
                            visa_sponsorship=detect_visa_sponsorship(blob),
                            apply_url=url,
                            source_url=url,
                            posted_at=posted_at,
                        )
                    )
                    if len(jobs) >= limit:
                        break
        return jobs

    @staticmethod
    def _company_from_title(title: str) -> str | None:
        if " at " in title.lower():
            return title.split(" at ")[-1].split("(")[0].strip()
        if " | " in title:
            return title.split(" | ")[0].strip()
        return None
