"""Single local user for personal use (no login required)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

DEFAULT_USER_EMAIL = "local@javacareer.ai"
DEFAULT_USER_NAME = "Ahsan Nadeem"
FALLBACK_USER_EMAIL = "demo@javacareer.ai"


async def ensure_default_user(db: AsyncSession) -> User:
    for email in (DEFAULT_USER_EMAIL, FALLBACK_USER_EMAIL):
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is not None and user.is_active:
            if user.full_name != DEFAULT_USER_NAME:
                user.full_name = DEFAULT_USER_NAME
                await db.flush()
            return user

    user = User(
        email=DEFAULT_USER_EMAIL,
        full_name=DEFAULT_USER_NAME,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    return user
