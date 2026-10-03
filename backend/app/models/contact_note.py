"""Private notes for companies and recruiters."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.db.types import UUIDStr


class ContactNote(Base):
    __tablename__ = "contact_notes"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", "recruiter_id", name="uq_contact_note_target"),
    )

    id: Mapped[str] = mapped_column(UUIDStr, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        UUIDStr, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    company_id: Mapped[Optional[str]] = mapped_column(
        UUIDStr, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    recruiter_id: Mapped[Optional[str]] = mapped_column(
        UUIDStr, ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=True, index=True
    )
    note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
