"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.default_user import ensure_default_user

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(db: DbSession) -> User:
    """Return the local default user — no login required."""
    return await ensure_default_user(db)


CurrentUser = Annotated[User, Depends(get_current_user)]
