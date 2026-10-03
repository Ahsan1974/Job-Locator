"""Authentication service."""

import hashlib
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import AuthProvider
from app.core.security import (
    TokenError,
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    hash_password,
    validate_token,
    verify_password,
)
from app.models.user import RefreshToken, User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    MessageResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.settings = get_settings()

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def register(self, data: UserCreate) -> TokenResponse:
        existing = await self.users.get_by_email(data.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = User(
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            auth_provider=AuthProvider.EMAIL.value,
            is_verified=False,
        )
        user = await self.users.create(user)
        return await self._issue_tokens(user)

    async def login(self, data: UserLogin) -> TokenResponse:
        user = await self.users.get_by_email(data.email)
        if user is None or not user.hashed_password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
        return await self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = validate_token(refresh_token, "refresh")
        except TokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

        stored = await self.users.get_refresh_token(self._hash_token(refresh_token))
        if stored is None or stored.expires_at < datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalid")

        user = await self.users.get_by_id(payload["sub"])
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        await self.users.revoke_refresh_token(stored)
        return await self._issue_tokens(user)

    async def forgot_password(self, email: str) -> MessageResponse:
        user = await self.users.get_by_email(email)
        # Always return success to avoid email enumeration
        if user and user.hashed_password:
            token = create_password_reset_token(user.email)
            # In production, send email. Log token in development for local testing.
            if self.settings.app_debug:
                print(f"[DEV] Password reset token for {email}: {token}")
        return MessageResponse(message="If that email exists, a reset link has been sent.")

    async def reset_password(self, token: str, new_password: str) -> MessageResponse:
        try:
            payload = validate_token(token, "password_reset")
        except TokenError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        user = await self.users.get_by_email(payload["sub"])
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        user.hashed_password = hash_password(new_password)
        await self.db.flush()
        return MessageResponse(message="Password updated successfully.")

    async def update_profile(self, user: User, data: UserUpdate) -> UserResponse:
        import json

        payload = data.model_dump(exclude_unset=True)
        if "preferred_countries" in payload and payload["preferred_countries"] is not None:
            payload["preferred_countries"] = json.dumps(payload["preferred_countries"])
        if "preferred_work_modes" in payload and payload["preferred_work_modes"] is not None:
            payload["preferred_work_modes"] = json.dumps(payload["preferred_work_modes"])
        for key, value in payload.items():
            setattr(user, key, value)
        await self.db.flush()
        await self.db.refresh(user)
        return UserResponse.model_validate(user)

    async def oauth_upsert(
        self,
        *,
        email: str,
        provider: AuthProvider,
        provider_id: str,
        full_name: str | None = None,
        avatar_url: str | None = None,
    ) -> TokenResponse:
        user = await self.users.get_by_email(email)
        if user is None:
            user = User(
                email=email.lower(),
                full_name=full_name,
                avatar_url=avatar_url,
                auth_provider=provider.value,
                provider_id=provider_id,
                is_verified=True,
            )
            user = await self.users.create(user)
        else:
            user.auth_provider = provider.value
            user.provider_id = provider_id
            if full_name:
                user.full_name = full_name
            if avatar_url:
                user.avatar_url = avatar_url
            user.is_verified = True
            await self.db.flush()
        return await self._issue_tokens(user)

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access = create_access_token(user.id, {"email": user.email})
        refresh = create_refresh_token(user.id)
        token_row = RefreshToken(
            user_id=user.id,
            token_hash=self._hash_token(refresh),
            expires_at=datetime.now(UTC)
            + timedelta(days=self.settings.refresh_token_expire_days),
        )
        await self.users.save_refresh_token(token_row)
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            user=UserResponse.model_validate(user),
        )
