"""Shared helpers for web-scraped job boards."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta

from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


def http_get(url: str, *, lang: str = "en-US,en;q=0.9") -> tuple[int, str]:
    try:
        from curl_cffi import requests as cffi_requests

        response = cffi_requests.get(url, impersonate="chrome120", timeout=40)
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
            "Accept-Language": lang,
        }
        response = httpx.get(url, headers=headers, timeout=40, follow_redirects=True)
        return response.status_code, response.text
    except Exception as exc:
        logger.debug("httpx GET failed %s: %s", url, exc)
        return 0, ""


def parse_posted_date(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            return datetime.strptime(raw, "%Y-%m-%d").replace(tzinfo=UTC)
        return date_parser.parse(raw).astimezone(UTC)
    except (ValueError, TypeError, OverflowError):
        pass

    t = raw.lower()
    now = datetime.now(UTC)
    if "just now" in t or "today" in t:
        return now
    if "yesterday" in t:
        return now - timedelta(days=1)
    m = re.search(r"(\d+)\s*(minute|hour|day|week|month|year)s?\s*ago", t)
    if m:
        amount = int(m.group(1))
        unit = m.group(2)
        deltas = {
            "minute": timedelta(minutes=amount),
            "hour": timedelta(hours=amount),
            "day": timedelta(days=amount),
            "week": timedelta(weeks=amount),
            "month": timedelta(days=amount * 30),
            "year": timedelta(days=amount * 365),
        }
        return now - deltas.get(unit, timedelta(days=amount))
    return None
