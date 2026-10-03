"""Company model and intelligence fields."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String, Text, func
from app.db.types import UUIDStr
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.recruiter import Recruiter


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(UUIDStr, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    headquarters_country: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    headquarters_city: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    technology_stack: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    funding_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hiring_trends: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avg_hiring_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    interview_difficulty: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    offers_visa_sponsorship: Mapped[Optional[bool]] = mapped_column(nullable=True)
    glassdoor_rating: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    jobs: Mapped[list["Job"]] = relationship(back_populates="company")
    recruiters: Mapped[list["Recruiter"]] = relationship(back_populates="company")
