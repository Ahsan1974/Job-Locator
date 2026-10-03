"""Seed demo user + Java jobs into local SQLite."""

import asyncio
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

# Ensure backend root on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal, init_db
from app.models.company import Company
from app.models.job import Job
from app.models.notification import Notification
from app.models.user import User
from app.repositories.company_repository import slugify


DEMO_JOBS = [
    {
        "title": "Senior Java Developer",
        "company": "Nordic Cloud Systems",
        "country": "Sweden",
        "city": "Stockholm",
        "work_mode": "hybrid",
        "visa_sponsorship": True,
        "salary_min": 75000,
        "salary_max": 95000,
        "salary_currency": "EUR",
        "experience_level": "senior",
        "stack": ["Java", "Spring Boot", "Kafka", "PostgreSQL", "AWS"],
        "description": "Build scalable microservices with Spring Boot and Kafka for our European platform.",
    },
    {
        "title": "Java Backend Engineer",
        "company": "Alpine Fintech",
        "country": "Switzerland",
        "city": "Zurich",
        "work_mode": "onsite",
        "visa_sponsorship": True,
        "salary_min": 120000,
        "salary_max": 150000,
        "salary_currency": "CHF",
        "experience_level": "mid",
        "stack": ["Java", "Spring", "Redis", "Kubernetes"],
        "description": "Design payment APIs and event-driven services for a regulated fintech.",
    },
    {
        "title": "Spring Boot Microservices Developer",
        "company": "RemoteForge",
        "country": "Germany",
        "city": "Berlin",
        "work_mode": "remote",
        "visa_sponsorship": False,
        "salary_min": 70000,
        "salary_max": 90000,
        "salary_currency": "EUR",
        "experience_level": "senior",
        "stack": ["Java 21", "Spring Boot", "Docker", "RabbitMQ"],
        "description": "Fully remote Spring Boot role building B2B SaaS integrations.",
    },
    {
        "title": "Java Software Engineer",
        "company": "Maple Data Labs",
        "country": "Canada",
        "city": "Toronto",
        "work_mode": "hybrid",
        "visa_sponsorship": True,
        "salary_min": 110000,
        "salary_max": 140000,
        "salary_currency": "CAD",
        "experience_level": "mid",
        "stack": ["Java", "Spring Boot", "MongoDB", "GCP"],
        "description": "Join our data platform team building Java services on GCP.",
    },
    {
        "title": "Java Cloud Engineer",
        "company": "Pacific Systems",
        "country": "Singapore",
        "city": "Singapore",
        "work_mode": "onsite",
        "visa_sponsorship": True,
        "salary_min": 90000,
        "salary_max": 130000,
        "salary_currency": "SGD",
        "experience_level": "senior",
        "stack": ["Java", "AWS", "ECS", "Terraform"],
        "description": "Cloud-native Java engineering with strong AWS focus and relocation support.",
    },
    {
        "title": "Java Architect",
        "company": "Emirates Digital",
        "country": "UAE",
        "city": "Dubai",
        "work_mode": "onsite",
        "visa_sponsorship": True,
        "salary_min": 25000,
        "salary_max": 35000,
        "salary_currency": "AED",
        "salary_period": "month",
        "experience_level": "architect",
        "stack": ["Java", "Spring Cloud", "Kubernetes", "Oracle"],
        "description": "Lead architecture for enterprise Java platforms across the GCC.",
    },
    {
        "title": "Senior Spring Boot Developer",
        "company": "London Lattice",
        "country": "United Kingdom",
        "city": "London",
        "work_mode": "hybrid",
        "visa_sponsorship": True,
        "salary_min": 75000,
        "salary_max": 100000,
        "salary_currency": "GBP",
        "experience_level": "senior",
        "stack": ["Java", "Spring Boot", "Kafka", "Docker", "AWS"],
        "description": "Own critical payment and ledger services in a regulated UK fintech.",
    },
    {
        "title": "Java Full Stack Developer",
        "company": "Karachi Tech Hub",
        "country": "Pakistan",
        "city": "Karachi",
        "work_mode": "remote",
        "visa_sponsorship": False,
        "salary_min": 2500,
        "salary_max": 4500,
        "salary_currency": "USD",
        "salary_period": "month",
        "experience_level": "mid",
        "stack": ["Java", "Spring Boot", "React", "PostgreSQL"],
        "description": "Remote Java full-stack role for product engineering teams.",
    },
]


async def seed() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "demo@javacareer.ai"))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                id=str(uuid4()),
                email="demo@javacareer.ai",
                hashed_password=hash_password("DemoPass123!"),
                full_name="Demo User",
                is_verified=True,
                is_active=True,
                visa_sponsorship_required=True,
            )
            session.add(user)
            await session.flush()
            session.add(
                Notification(
                    user_id=user.id,
                    title="Welcome to Java Career AI",
                    body="Upload your resume and refresh jobs to get personalized match scores.",
                    notification_type="info",
                    link="/resume",
                )
            )

        for item in DEMO_JOBS:
            company_result = await session.execute(
                select(Company).where(Company.name == item["company"])
            )
            company = company_result.scalar_one_or_none()
            if company is None:
                company = Company(
                    id=str(uuid4()),
                    name=item["company"],
                    slug=slugify(item["company"]),
                    headquarters_country=item["country"],
                    headquarters_city=item["city"],
                    offers_visa_sponsorship=item["visa_sponsorship"],
                    technology_stack=json.dumps(item["stack"]),
                    industry="Technology",
                    description=f"{item['company']} hires Java engineers globally.",
                )
                session.add(company)
                await session.flush()

            ext_id = f"seed-{slugify(item['title'])}-{slugify(item['company'])}"
            job_result = await session.execute(
                select(Job).where(Job.source == "seed", Job.external_id == ext_id)
            )
            if job_result.scalar_one_or_none():
                continue

            session.add(
                Job(
                    id=str(uuid4()),
                    company_id=company.id,
                    title=item["title"],
                    description=item["description"],
                    requirements=f"Experience with {', '.join(item['stack'])}",
                    technology_stack=json.dumps(item["stack"]),
                    country=item["country"],
                    city=item["city"],
                    location_raw=f"{item['city']}, {item['country']}",
                    work_mode=item["work_mode"],
                    employment_type="full_time",
                    experience_level=item["experience_level"],
                    visa_sponsorship=item["visa_sponsorship"],
                    relocation=item["visa_sponsorship"],
                    salary_min=Decimal(item["salary_min"]),
                    salary_max=Decimal(item["salary_max"]),
                    salary_currency=item["salary_currency"],
                    salary_period=item.get("salary_period", "year"),
                    source="seed",
                    external_id=ext_id,
                    apply_url=None,
                    source_url=None,
                    posted_at=datetime.now(UTC),
                    is_active=False,
                    recommendation_score=Decimal("82.5"),
                    recommendation_priority="high",
                    match_score=Decimal("78.0"),
                )
            )

        await session.commit()
        print("Seed complete.")
        print("Login: demo@javacareer.ai / DemoPass123!")


if __name__ == "__main__":
    asyncio.run(seed())
