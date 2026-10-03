"""Timezone helpers for consistent datetime handling."""

from __future__ import annotations

from datetime import UTC, datetime


def ensure_utc(dt: datetime) -> datetime:
    """Normalize naive or aware datetimes to UTC-aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def posted_at_is_newer(candidate: datetime | None, existing: datetime | None) -> bool:
    if candidate is None:
        return False
    if existing is None:
        return True
    return ensure_utc(candidate) > ensure_utc(existing)
