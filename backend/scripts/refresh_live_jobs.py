"""Deactivate placeholder demo jobs and fetch live jobs."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import update

from app.db.session import AsyncSessionLocal, init_db
from app.models.job import Job
from app.services.ingestion_service import refresh_all_jobs


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Job).where(Job.apply_url.like("%example.com%")).values(is_active=False)
        )
        await session.execute(update(Job).where(Job.source == "seed").values(is_active=False))
        await session.commit()
    print("Deactivated placeholder jobs.")
    stats = await refresh_all_jobs()
    print("Live job refresh:", stats)


if __name__ == "__main__":
    asyncio.run(main())
