"""Company repository."""

import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "company"


class CompanyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_name(self, name: str) -> Company | None:
        result = await self.db.execute(select(Company).where(Company.name == name))
        return result.scalar_one_or_none()

    async def get_by_name_insensitive(self, name: str) -> Company | None:
        result = await self.db.execute(
            select(Company).where(func.lower(Company.name) == name.lower())
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        name: str,
        *,
        website: str | None = None,
        logo_url: str | None = None,
        country: str | None = None,
    ) -> Company:
        clean_name = name.strip()
        slug = slugify(clean_name)

        existing = await self.get_by_slug(slug)
        if existing is None:
            existing = await self.get_by_name_insensitive(clean_name)
        if existing is None:
            existing = await self.get_by_name(clean_name)

        if existing:
            if website and not existing.website:
                existing.website = website
            if logo_url and not existing.logo_url:
                existing.logo_url = logo_url
            if country and not existing.headquarters_country:
                existing.headquarters_country = country
            await self.db.flush()
            return existing

        company = Company(
            name=clean_name,
            slug=slug,
            website=website,
            logo_url=logo_url,
            headquarters_country=country,
        )
        self.db.add(company)
        await self.db.flush()
        await self.db.refresh(company)
        return company

    async def get_by_slug(self, slug: str) -> Company | None:
        result = await self.db.execute(select(Company).where(Company.slug == slug))
        return result.scalar_one_or_none()

    async def list_companies(self, limit: int = 50, offset: int = 0) -> list[Company]:
        result = await self.db.execute(
            select(Company).order_by(Company.name).offset(offset).limit(limit)
        )
        return list(result.scalars().all())
