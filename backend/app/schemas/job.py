"""Job-related Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CompanyBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    logo_url: str | None = None
    website: str | None = None
    industry: str | None = None
    company_size: str | None = None
    offers_visa_sponsorship: bool | None = None


class RecruiterBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str | None = None
    linkedin_url: str | None = None
    title: str | None = None


class JobListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    country: str | None = None
    city: str | None = None
    work_mode: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    visa_sponsorship: bool
    relocation: bool
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_currency: str
    salary_estimated: bool
    source: str
    apply_url: str | None = None
    posted_at: datetime | None = None
    match_score: Decimal | None = None
    recommendation_score: Decimal | None = None
    recommendation_priority: str | None = None
    company: CompanyBrief | None = None


class JobDetail(JobListItem):
    description: str | None = None
    responsibilities: str | None = None
    requirements: str | None = None
    preferred_skills: str | None = None
    benefits: str | None = None
    technology_stack: str | None = None
    location_raw: str | None = None
    salary_period: str | None = None
    salary_confidence: Decimal | None = None
    source_url: str | None = None
    expires_at: date | None = None
    is_active: bool
    created_at: datetime
    recruiter: RecruiterBrief | None = None


class JobSearchParams(BaseModel):
    q: str | None = None
    work_mode: str | None = None
    country: str | None = None
    city: str | None = None
    visa_sponsorship: bool | None = None
    relocation: bool | None = None
    experience_level: str | None = None
    employment_type: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    company: str | None = None
    source: str | None = None
    added_today: bool | None = Field(
        default=None, description="Only jobs first added to the database today (UTC)"
    )
    posted_within: str | None = Field(
        default=None, description="today | week | month"
    )
    sort_by: str = "posted_at"
    sort_order: str = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedJobs(BaseModel):
    items: list[JobListItem]
    total: int
    page: int
    page_size: int
    pages: int


class DashboardStats(BaseModel):
    total_jobs: int
    jobs_added_today: int
    remote_jobs: int
    visa_sponsorship_jobs: int
    average_salary: float | None
    countries_count: int
    companies_hiring: int
    saved_jobs: int
    applications: int
    recommended_jobs: int


class ActivityItem(BaseModel):
    id: str
    type: str
    title: str
    subtitle: str | None = None
    timestamp: datetime
    link: str | None = None
