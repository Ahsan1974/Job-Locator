"""Application configuration — local-first, no Docker required."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parents[3]
_DATA = _ROOT / "data"
_DATA.mkdir(parents=True, exist_ok=True)
_DEFAULT_DB = f"sqlite+aiosqlite:///{(_DATA / 'java_career_ai.db').as_posix()}"
_DEFAULT_DB_SYNC = f"sqlite:///{(_DATA / 'java_career_ai.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", str(_ROOT / ".env")),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Job Hunter"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    api_prefix: str = "/api/v1"
    secret_key: str = Field(default="dev-secret-change-in-production-min-64-chars-xxxxxxxxxxxx")
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    algorithm: str = "HS256"

    # Default: local SQLite (no Docker / no Postgres required)
    database_url: str = _DEFAULT_DB
    database_url_sync: str = _DEFAULT_DB_SYNC

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/api/v1/auth/github/callback"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@javacareer.ai"
    smtp_tls: bool = True

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = ""

    # Groq (OpenAI-compatible) — key format gsk_...
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # Adzuna official API (optional)
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""

    # Jooble aggregates Indeed, LinkedIn, Monster, etc. (free key at jooble.org/api/about)
    jooble_api_key: str = ""

    # Careerjet affiliate API (careerjet.com/partners/api)
    careerjet_api_key: str = ""

    # JSearch via RapidAPI (optional)
    jsearch_rapidapi_key: str = ""

    # Scrape Indeed PK + Rozee for Pakistan Java roles
    enable_pakistan_scraping: bool = True

    # LinkedIn public guest job search (no login; may be rate-limited by LinkedIn)
    enable_linkedin_scraping: bool = True
    linkedin_fetch_limit: int = 36

    # Fetch live jobs on API startup
    refresh_jobs_on_startup: bool = True
    job_fetch_limit_per_source: int = 40
    pakistan_fetch_limit: int = 24
    usajobs_api_key: str = ""
    usajobs_user_agent: str = "JavaCareerAI/1.0"

    discord_webhook_url: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Optional Web Push configuration. Generate a VAPID key pair before deploying
    # the installable app over HTTPS.
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:local@jobhunter.app"

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    upload_dir: str = str(_ROOT / "data" / "uploads")
    max_upload_size_mb: int = 10

    # Local scheduler (replaces Celery/Redis)
    job_refresh_minutes: int = 60
    enable_scheduler: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def has_llm(self) -> bool:
        return self.has_groq or self.has_openai

    @property
    def llm_api_key(self) -> str:
        return self.groq_api_key or self.openai_api_key

    @property
    def llm_base_url(self) -> str | None:
        if self.groq_api_key:
            return self.groq_base_url
        return self.openai_base_url or None

    @property
    def llm_model(self) -> str:
        return self.groq_model if self.groq_api_key else self.openai_model


@lru_cache
def get_settings() -> Settings:
    return Settings()
