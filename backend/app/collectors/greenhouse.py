"""Greenhouse Job Board public API — many YC/tech companies."""

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

# Public board tokens (company slug on boards.greenhouse.io)
GREENHOUSE_BOARDS = (
    "stripe", "airbnb", "coinbase", "datadog", "dropbox", "figma", "gitlab",
    "mongodb", "okta", "plaid", "reddit", "robinhood", "shopify", "square",
    "twilio", "unity", "vercel", "wise", "zapier", "brex", "chime", "discord",
    "duolingo", "hubspot", "instacart", "lyft", "pinterest", "spotify",
)


class GreenhouseConnector(JobSourceConnector):
    name = "greenhouse"

    async def fetch(self, query: str = "java", limit: int = 50) -> list[RawJob]:
        jobs: list[RawJob] = []
        seen: set[str] = set()
        headers = {"User-Agent": "JavaCareerAI/1.0"}

        async with httpx.AsyncClient(timeout=45.0, headers=headers) as client:
            for board in GREENHOUSE_BOARDS:
                if len(jobs) >= limit:
                    break
                url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
                try:
                    response = await client.get(url, params={"content": "true"})
                    if response.status_code == 404:
                        continue
                    response.raise_for_status()
                    payload = response.json()
                except Exception:
                    continue

                for item in payload.get("jobs", []):
                    title = item.get("title") or ""
                    content = (item.get("content") or "")[:5000]
                    if not is_java_related_from_aggregator(title, content):
                        continue
                    ext_id = str(item.get("id") or f"{board}-{title}")
                    if ext_id in seen:
                        continue
                    seen.add(ext_id)

                    loc = item.get("location", {}).get("name") if isinstance(item.get("location"), dict) else item.get("location")
                    apply_url = item.get("absolute_url")
                    posted_at = None
                    if item.get("updated_at"):
                        try:
                            posted_at = datetime.fromisoformat(str(item["updated_at"]).replace("Z", "+00:00"))
                        except ValueError:
                            posted_at = None

                    blob = f"{title} {content} {loc or ''}"
                    jobs.append(
                        RawJob(
                            source=self.name,
                            external_id=ext_id,
                            title=title,
                            description=content,
                            company_name=board.replace("-", " ").title(),
                            location_raw=str(loc) if loc else None,
                            country=normalize_country(str(loc).split(",")[-1].strip() if loc else None),
                            work_mode=detect_work_mode(blob),
                            experience_level=detect_experience_level(title, content),
                            visa_sponsorship=detect_visa_sponsorship(blob),
                            apply_url=apply_url,
                            source_url=apply_url,
                            posted_at=posted_at,
                        )
                    )
                    if len(jobs) >= limit:
                        break
        return jobs
