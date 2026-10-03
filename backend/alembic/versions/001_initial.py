"""Initial schema — Phase 1

Revision ID: 001_initial
Revises:
Create Date: 2026-07-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(1024), nullable=True),
        sa.Column("auth_provider", sa.String(32), nullable=False, server_default="email"),
        sa.Column("provider_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("preferred_countries", sa.Text(), nullable=True),
        sa.Column("preferred_work_modes", sa.Text(), nullable=True),
        sa.Column("salary_expectation_min", sa.Integer(), nullable=True),
        sa.Column("salary_expectation_max", sa.Integer(), nullable=True),
        sa.Column("salary_currency", sa.String(8), server_default="USD"),
        sa.Column("visa_sponsorship_required", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("theme", sa.String(16), server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    op.create_table(
        "companies",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(128), nullable=True),
        sa.Column("company_size", sa.String(64), nullable=True),
        sa.Column("website", sa.String(1024), nullable=True),
        sa.Column("logo_url", sa.String(1024), nullable=True),
        sa.Column("headquarters_country", sa.String(64), nullable=True),
        sa.Column("headquarters_city", sa.String(128), nullable=True),
        sa.Column("technology_stack", sa.Text(), nullable=True),
        sa.Column("funding_info", sa.Text(), nullable=True),
        sa.Column("hiring_trends", sa.Text(), nullable=True),
        sa.Column("avg_hiring_days", sa.Integer(), nullable=True),
        sa.Column("interview_difficulty", sa.String(32), nullable=True),
        sa.Column("offers_visa_sponsorship", sa.Boolean(), nullable=True),
        sa.Column("glassdoor_rating", sa.String(16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_companies_name", "companies", ["name"], unique=True)
    op.create_index("ix_companies_slug", "companies", ["slug"], unique=True)

    op.create_table(
        "recruiters",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("company_id", sa.UUID(as_uuid=False), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("linkedin_url", sa.String(1024), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "skills",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("aliases", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_skills_name"),
    )
    op.create_index("ix_skills_name", "skills", ["name"])

    op.create_table(
        "technologies",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_technologies_name"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("company_id", sa.UUID(as_uuid=False), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recruiter_id", sa.UUID(as_uuid=False), sa.ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("preferred_skills", sa.Text(), nullable=True),
        sa.Column("benefits", sa.Text(), nullable=True),
        sa.Column("technology_stack", sa.Text(), nullable=True),
        sa.Column("country", sa.String(64), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("location_raw", sa.String(512), nullable=True),
        sa.Column("work_mode", sa.String(32), nullable=True),
        sa.Column("employment_type", sa.String(32), nullable=True),
        sa.Column("experience_level", sa.String(32), nullable=True),
        sa.Column("visa_sponsorship", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("relocation", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_currency", sa.String(8), server_default="USD"),
        sa.Column("salary_period", sa.String(16), nullable=True),
        sa.Column("salary_estimated", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("salary_confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("apply_url", sa.String(2048), nullable=True),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("match_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("recommendation_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("recommendation_priority", sa.String(16), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source", "external_id", name="uq_jobs_source_external_id"),
    )
    op.create_index("ix_jobs_title", "jobs", ["title"])
    op.create_index("ix_jobs_posted_at", "jobs", ["posted_at"])
    op.create_index("ix_jobs_country", "jobs", ["country"])
    op.create_index("ix_jobs_work_mode", "jobs", ["work_mode"])
    op.create_index("ix_jobs_visa", "jobs", ["visa_sponsorship"])
    op.create_index("ix_jobs_experience", "jobs", ["experience_level"])
    op.create_index("ix_jobs_source", "jobs", ["source"])
    op.create_index("ix_jobs_is_active", "jobs", ["is_active"])
    op.create_index("ix_jobs_content_hash", "jobs", ["content_hash"])
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"])

    # Full-text search trigger
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_jobs_search_vector ON jobs USING GIN (search_vector);
        CREATE OR REPLACE FUNCTION jobs_search_vector_update() RETURNS trigger AS $$
        BEGIN
          NEW.search_vector :=
            setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(NEW.requirements, '')), 'C') ||
            setweight(to_tsvector('english', coalesce(NEW.technology_stack, '')), 'B');
          RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        DROP TRIGGER IF EXISTS trg_jobs_search_vector ON jobs;
        CREATE TRIGGER trg_jobs_search_vector
        BEFORE INSERT OR UPDATE ON jobs
        FOR EACH ROW EXECUTE FUNCTION jobs_search_vector_update();
        """
    )

    op.create_table(
        "job_skills",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("job_id", sa.UUID(as_uuid=False), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", sa.UUID(as_uuid=False), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("years_required", sa.Integer(), nullable=True),
        sa.UniqueConstraint("job_id", "skill_id", name="uq_job_skills"),
    )

    op.create_table(
        "resumes",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("parsed_json", sa.Text(), nullable=True),
        sa.Column("skills", sa.Text(), nullable=True),
        sa.Column("technologies", sa.Text(), nullable=True),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("education", sa.Text(), nullable=True),
        sa.Column("projects", sa.Text(), nullable=True),
        sa.Column("certifications", sa.Text(), nullable=True),
        sa.Column("languages", sa.Text(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])

    op.create_table(
        "resume_embeddings",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("resume_id", sa.UUID(as_uuid=False), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("vector_id", sa.String(128), nullable=True),
        sa.Column("chunk_index", sa.Integer(), server_default="0"),
        sa.Column("chunk_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "applications",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.UUID(as_uuid=False), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="applied"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("history", sa.Text(), nullable=True),
        sa.Column("reminder_date", sa.Date(), nullable=True),
        sa.Column("cover_letter", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "job_id", name="uq_applications_user_job"),
    )
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_index("ix_applications_job_id", "applications", ["job_id"])
    op.create_index("ix_applications_status", "applications", ["status"])

    op.create_table(
        "saved_jobs",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.UUID(as_uuid=False), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "job_id", name="uq_saved_jobs_user_job"),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("query", sa.String(512), nullable=True),
        sa.Column("filters_json", sa.Text(), nullable=True),
        sa.Column("channels", sa.Text(), nullable=True),
        sa.Column("min_match_score", sa.Integer(), nullable=True),
        sa.Column("visa_only", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("remote_only", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("link", sa.String(1024), nullable=True),
        sa.Column("channel", sa.String(32), server_default="dashboard"),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_jobs_search_vector ON jobs;")
    op.execute("DROP FUNCTION IF EXISTS jobs_search_vector_update();")
    for table in (
        "notifications",
        "alerts",
        "saved_jobs",
        "applications",
        "resume_embeddings",
        "resumes",
        "job_skills",
        "jobs",
        "technologies",
        "skills",
        "recruiters",
        "companies",
        "refresh_tokens",
        "users",
    ):
        op.drop_table(table)
