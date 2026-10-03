"""Job posting models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.types import UUIDStr

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.company import Company
    from app.models.recruiter import Recruiter
    from app.models.saved_job import SavedJob


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_jobs_source_external_id"),
        Index("ix_jobs_posted_at", "posted_at"),
        Index("ix_jobs_country", "country"),
        Index("ix_jobs_work_mode", "work_mode"),
        Index("ix_jobs_visa", "visa_sponsorship"),
        Index("ix_jobs_experience", "experience_level"),
    )

    id: Mapped[str] = mapped_column(UUIDStr, primary_key=True, default=lambda: str(uuid4()))
    company_id: Mapped[Optional[str]] = mapped_column(
        UUIDStr, ForeignKey("companies.id", ondelete="SET NULL"), index=True
    )
    recruiter_id: Mapped[Optional[str]] = mapped_column(
        UUIDStr, ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    benefits: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    technology_stack: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list

    country: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    location_raw: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    work_mode: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # remote/hybrid/onsite
    employment_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    experience_level: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    visa_sponsorship: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    relocation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    salary_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    salary_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(8), default="USD")
    salary_period: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # year/month/hour
    salary_estimated: Mapped[bool] = mapped_column(Boolean, default=False)
    salary_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    apply_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # Precomputed scores (Phase 2/3 populate these)
    match_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    recommendation_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    recommendation_priority: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    search_vector: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    company: Mapped[Optional["Company"]] = relationship(back_populates="jobs")
    recruiter: Mapped[Optional["Recruiter"]] = relationship(back_populates="jobs")
    skills: Mapped[list["JobSkill"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(back_populates="job")
    saved_by: Mapped[list["SavedJob"]] = relationship(back_populates="job")


class JobSkill(Base):
    __tablename__ = "job_skills"
    __table_args__ = (UniqueConstraint("job_id", "skill_id", name="uq_job_skills"),)

    id: Mapped[str] = mapped_column(UUIDStr, primary_key=True, default=lambda: str(uuid4()))
    job_id: Mapped[str] = mapped_column(
        UUIDStr, ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )
    skill_id: Mapped[str] = mapped_column(
        UUIDStr, ForeignKey("skills.id", ondelete="CASCADE"), index=True
    )
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    years_required: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    job: Mapped["Job"] = relationship(back_populates="skills")
