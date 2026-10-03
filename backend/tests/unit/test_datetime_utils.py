"""Tests for datetime normalization."""

from datetime import UTC, datetime

from app.domain.datetime_utils import ensure_utc, posted_at_is_newer


def test_ensure_utc_naive():
    naive = datetime(2026, 3, 1, 12, 0, 0)
    result = ensure_utc(naive)
    assert result.tzinfo is UTC
    assert result.year == 2026


def test_posted_at_is_newer_mixed_tz():
    naive_old = datetime(2025, 1, 1)
    aware_new = datetime(2026, 1, 1, tzinfo=UTC)
    assert posted_at_is_newer(aware_new, naive_old)
    assert not posted_at_is_newer(naive_old, aware_new)
