"""Shared SQLAlchemy column helpers — SQLite + Postgres portable."""

from sqlalchemy import String

# Store UUIDs as 36-char strings for SQLite compatibility
UUIDStr = String(36)
