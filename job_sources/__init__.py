"""Job source connectors package.

Production connectors live in `backend/app/collectors/`.
This package re-exports them for the documented project layout.

Legal note: Only official APIs and publicly permitted feeds are enabled.
Sources that require ToS-restricted scraping are registered as stubs.
"""

from app.collectors.arbeitnow import ArbeitnowConnector
from app.collectors.base import JobSourceConnector, RawJob
from app.collectors.remoteok import RemoteOKConnector
from app.collectors.remotive import RemotiveConnector
from app.collectors.usajobs import USAJobsConnector

# Sources planned for future API/partner integrations (stubs — not scraped)
PLANNED_SOURCES = [
    "indeed",
    "linkedin",
    "google_jobs",
    "ziprecruiter",
    "monster",
    "careerbuilder",
    "glassdoor",
    "simplyhired",
    "jooble",
    "linkup",
    "wellfound",
    "dice",
    "builtin",
    "crunchboard",
    "levels_fyi",
    "remote_co",
    "we_work_remotely",
    "working_nomads",
    "hubstaff_talent",
    "jobgether",
    "github_careers",
    "ycombinator",
    "naukri",
    "stepstone",
    "seek",
    "reed",
    "bayt",
    "gulftalent",
    "jobstreet",
    "totaljobs",
    "handshake",
    "idealist",
    "the_muse",
    "execthread",
    "company_career_pages",
]

ACTIVE_CONNECTORS = [
    RemoteOKConnector,
    RemotiveConnector,
    ArbeitnowConnector,
    USAJobsConnector,
]

__all__ = [
    "JobSourceConnector",
    "RawJob",
    "RemoteOKConnector",
    "RemotiveConnector",
    "ArbeitnowConnector",
    "USAJobsConnector",
    "ACTIVE_CONNECTORS",
    "PLANNED_SOURCES",
]
