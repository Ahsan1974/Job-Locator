"""Pull extra freelance and Pakistan jobs into the local database."""

import asyncio
import logging

from app.db.session import AsyncSessionLocal
from app.services.default_user import ensure_default_user
from app.services.ingestion_service import JobIngestionService

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    async with AsyncSessionLocal() as session:
        user = await ensure_default_user(session)
        await session.commit()
        print("user", user.full_name)
        service = JobIngestionService(session)
        freelance = await service.refresh_by_source("freelance", limit=60)
        print("freelance", freelance)
        pakistan = await service.refresh_by_source("pakistan", limit=40)
        print("pakistan", pakistan)


if __name__ == "__main__":
    asyncio.run(main())
