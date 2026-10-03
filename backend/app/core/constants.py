"""Shared domain enums and constants."""

from enum import StrEnum


class WorkMode(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class EmploymentType(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    PERMANENT = "permanent"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"


class ExperienceLevel(StrEnum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"
    ARCHITECT = "architect"


class ApplicationStatus(StrEnum):
    SAVED = "saved"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertChannel(StrEnum):
    DASHBOARD = "dashboard"
    EMAIL = "email"
    DESKTOP = "desktop"
    DISCORD = "discord"
    TELEGRAM = "telegram"


class AuthProvider(StrEnum):
    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"


# Target countries for Phase 1 filtering (India excluded from UI)
TARGET_COUNTRIES: frozenset[str] = frozenset(
    {
        "USA",
        "Canada",
        "Germany",
        "United Kingdom",
        "Ireland",
        "Netherlands",
        "Switzerland",
        "Sweden",
        "Norway",
        "Denmark",
        "Finland",
        "Australia",
        "New Zealand",
        "Singapore",
        "Japan",
        "South Korea",
        "UAE",
        "Saudi Arabia",
        "Qatar",
        "Pakistan",
    }
)

# Java-related title keywords — only collect matching jobs
JAVA_TITLE_KEYWORDS: tuple[str, ...] = (
    "java developer",
    "senior java",
    "java backend",
    "spring boot",
    "java software engineer",
    "backend java",
    "java full stack",
    "java fullstack",
    "java microservices",
    "java cloud",
    "java api",
    "j2ee",
    "spring framework",
    "java architect",
    "software engineer java",
    "java engineer",
    "jvm",
    "kotlin",  # often adjacent; filtered further in matcher
)

JAVA_REQUIRED_TERMS: tuple[str, ...] = ("java", "spring", "jvm", "j2ee", "jakarta ee")
