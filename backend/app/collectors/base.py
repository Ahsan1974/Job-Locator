"""Normalized raw job DTO and connector ABC."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class RawJob:
    source: str
    external_id: str
    title: str
    description: str | None = None
    company_name: str | None = None
    company_website: str | None = None
    company_logo: str | None = None
    country: str | None = None
    city: str | None = None
    location_raw: str | None = None
    work_mode: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    visa_sponsorship: bool = False
    relocation: bool = False
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_currency: str = "USD"
    salary_period: str | None = None
    apply_url: str | None = None
    source_url: str | None = None
    posted_at: datetime | None = None
    technology_stack: list[str] = field(default_factory=list)
    requirements: str | None = None
    benefits: str | None = None


class JobSourceConnector(ABC):
    """Use official APIs or publicly permitted feeds only."""

    name: str
    enabled: bool = True

    @abstractmethod
    async def fetch(self, query: str = "Java Spring Boot", limit: int = 50) -> list[RawJob]:
        ...
