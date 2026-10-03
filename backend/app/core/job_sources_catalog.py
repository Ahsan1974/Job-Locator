"""Catalog of the top 50 job boards and how this app connects to each."""

from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True)
class SourceInfo:
    id: str
    name: str
    category: str
    status: str  # active | needs_key | blocked | partial
    note: str


def get_sources_catalog() -> list[SourceInfo]:
    settings = get_settings()
    return [
        SourceInfo("jooble", "Jooble", "Aggregator", "needs_key" if not settings.jooble_api_key else "active",
                   "Aggregates Indeed, LinkedIn, Monster & more. Free key: jooble.org/api/about"),
        SourceInfo("adzuna", "Adzuna", "Aggregator", "needs_key" if not settings.adzuna_app_id else "active",
                   "Multi-country API. Free keys: developer.adzuna.com"),
        SourceInfo("careerjet", "Careerjet", "Aggregator", "needs_key" if not settings.careerjet_api_key else "active",
                   "Global search API. Register: careerjet.com/partners/api"),
        SourceInfo("remoteok", "RemoteOK", "Remote", "active", "Public API — Java roles vary by day"),
        SourceInfo("remotive", "Remotive", "Remote", "active", "Public API"),
        SourceInfo("weworkremotely", "We Work Remotely", "Remote", "active", "Official RSS feed"),
        SourceInfo("jobicy", "Jobicy", "Remote", "active", "Public API with Java/Spring tags"),
        SourceInfo("himalayas", "Himalayas", "Remote", "active", "Public jobs API"),
        SourceInfo("arbeitnow", "Arbeitnow", "Regional", "active", "European tech jobs API"),
        SourceInfo("workingnomads", "Working Nomads", "Remote", "active", "Public JSON API"),
        SourceInfo("usajobs", "USAJobs", "Government", "needs_key" if not settings.usajobs_api_key else "active",
                   "US federal jobs — requires API key"),
        SourceInfo("findwork", "Findwork", "Tech", "partial", "Dev API — optional token"),
        SourceInfo("indeed", "Indeed", "Global Giant", "blocked",
                   "No public scrape API. Use Jooble/Adzuna aggregators instead"),
        SourceInfo("linkedin", "LinkedIn Jobs", "Global Giant",
                   "active" if settings.enable_linkedin_scraping else "blocked",
                   "Public guest search — onsite & remote Java roles worldwide"),
        SourceInfo("ziprecruiter", "ZipRecruiter", "Global Giant", "blocked", "Partner API only"),
        SourceInfo("monster", "Monster", "Global Giant", "blocked", "No open public API"),
        SourceInfo("careerbuilder", "CareerBuilder", "Global Giant", "blocked", "Partner integrations only"),
        SourceInfo("glassdoor", "Glassdoor", "Global Giant", "blocked", "No public job API"),
        SourceInfo("google_jobs", "Google for Jobs", "Aggregator", "blocked", "No public indexing API"),
        SourceInfo("simplyhired", "SimplyHired", "Aggregator", "blocked", "Indeed-owned; no public API"),
        SourceInfo("linkup", "LinkUp", "Aggregator", "blocked", "Commercial API only"),
        SourceInfo("wellfound", "Wellfound (AngelList)", "Startup", "blocked", "No official public API"),
        SourceInfo("dice", "Dice", "Tech", "blocked", "No reliable public feed"),
        SourceInfo("levels", "Levels.fyi", "Tech", "blocked", "Comp data focus; no open jobs API"),
        SourceInfo("github_jobs", "GitHub Jobs", "Tech", "blocked", "Service discontinued"),
        SourceInfo("yc_startups", "Y Combinator / Work at a Startup", "Startup", "blocked",
                   "Requires reverse-engineered session; not stable"),
        SourceInfo("flexjobs", "FlexJobs", "Remote", "blocked", "Paid/vetted platform; no public API"),
        SourceInfo("remote_co", "Remote.co", "Remote", "partial", "RSS attempted; feed often unavailable"),
        SourceInfo("remote_ok", "Remote OK", "Remote", "active", "Same as remoteok connector"),
        SourceInfo("jobgether", "Jobgether", "Remote", "blocked", "No public API documented"),
        SourceInfo("hubstaff", "Hubstaff Talent", "Remote", "blocked", "No public jobs API"),
        SourceInfo("upwork", "Upwork", "Freelance", "blocked", "Freelance marketplace; separate API with approval"),
        SourceInfo("fiverr", "Fiverr", "Freelance", "blocked", "Gig marketplace, not job board API"),
        SourceInfo("naukri", "Naukri", "Regional (India)", "blocked", "No open public API"),
        SourceInfo("stepstone", "StepStone", "Regional (EU)", "blocked", "Commercial feeds only"),
        SourceInfo("seek", "SEEK", "Regional (AU/NZ)", "blocked", "Partner API only"),
        SourceInfo("reed", "Reed.co.uk", "Regional (UK)", "blocked", "Partner API only"),
        SourceInfo("gulftalent", "GulfTalent", "Regional (MENA)", "blocked", "No public API"),
        SourceInfo("bayt", "Bayt.com", "Regional (MENA)", "blocked", "No public API"),
        SourceInfo("jobstreet", "JobStreet", "Regional (SEA)", "blocked", "Partner API only"),
        SourceInfo("handshake", "Handshake", "College", "blocked", "University-only platform"),
        SourceInfo("themuse", "The Muse", "Niche", "blocked", "Partner integrations only"),
        SourceInfo("efinancial", "eFinancialCareers", "Niche", "blocked", "No public API"),
        SourceInfo("idealist", "Idealist", "Niche", "blocked", "Non-profit focus; no public API"),
    ]


def sources_status_payload() -> dict:
    catalog = get_sources_catalog()
    active = [s for s in catalog if s.status == "active"]
    needs_key = [s for s in catalog if s.status == "needs_key"]
    return {
        "total_catalogued": len(catalog),
        "active_now": len(active),
        "needs_api_key": len(needs_key),
        "sources": [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "status": s.status,
                "note": s.note,
            }
            for s in catalog
        ],
    }
