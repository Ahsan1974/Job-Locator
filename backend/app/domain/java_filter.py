"""Java job relevance filter — only keep Java/Spring related roles."""

import re

from app.core.constants import JAVA_REQUIRED_TERMS, JAVA_TITLE_KEYWORDS


def _mentions_java(text: str) -> bool:
    """True for Java the language, not JavaScript/TypeScript."""
    if re.search(r"\bjavascript\b", text):
        return False
    if re.search(r"\btypescript\b", text) and not re.search(r"\bjava\b", text):
        return False
    return bool(re.search(r"\bjava\b", text))


PYTHON_TITLE_KEYWORDS: tuple[str, ...] = (
    "python developer",
    "python engineer",
    "python backend",
    "django",
    "fastapi",
    "flask developer",
)

AI_TITLE_KEYWORDS: tuple[str, ...] = (
    "machine learning",
    "ml engineer",
    "ai engineer",
    "artificial intelligence",
    "data scientist",
    "deep learning",
    "nlp engineer",
    "computer vision",
    "llm ",
    "generative ai",
    "prompt engineer",
    "pytorch",
    "tensorflow",
)


def _is_qa_or_pm(title_l: str, desc_l: str) -> bool:
    if any(
        x in title_l
        for x in (
            "qa engineer",
            "qa tester",
            "sdet",
            "quality assurance",
            "test automation",
            "software tester",
            "quality engineer",
            "manual tester",
        )
    ):
        return True
    if any(x in title_l for x in ("project manager", "scrum master", "product owner", "program manager")):
        blob = f"{title_l} {desc_l[:800]}"
        return any(
            x in blob
            for x in ("software", "agile", "scrum", "jira", "java", "python", "technical", "it ", "developer", "engineer")
        )
    return False


def is_software_gig(title: str, description: str | None = None) -> bool:
    """Broad match for freelance software work, not only Java."""
    blob = f"{title or ''} {description or ''}"[:900].lower()
    terms = (
        "java", "python", "developer", "software", "programmer", "web ", "website",
        "react", "node", "angular", "vue", "django", "spring", "api", "backend",
        "frontend", "full stack", "fullstack", "mobile", "android", "ios", "qa",
        "tester", "bug", "wordpress", "shopify", "devops", "machine learning",
        "artificial intelligence", "data scien", "script", "coding", "app ",
    )
    return any(term in blob for term in terms)


def _is_python_or_ai(title_l: str, desc_l: str) -> bool:
    blob = f"{title_l} {desc_l[:800]}"
    if any(kw in title_l for kw in PYTHON_TITLE_KEYWORDS + AI_TITLE_KEYWORDS):
        return True
    if re.search(r"\bpython\b", title_l) and re.search(
        r"\b(developer|engineer|backend|scientist|programmer)\b", title_l
    ):
        return True
    if re.search(r"\b(python|pytorch|tensorflow|langchain|llm)\b", blob) and re.search(
        r"\b(developer|engineer|scientist|backend)\b", title_l
    ):
        return True
    return False


def is_java_related_job(title: str, description: str | None = None) -> bool:
    """Return True for Java, Python, or AI / ML software roles."""
    title_l = (title or "").lower()
    desc_l = (description or "").lower()
    blob = f"{title_l} {desc_l}"

    if _is_python_or_ai(title_l, desc_l) or _is_qa_or_pm(title_l, desc_l):
        return True

    if any(kw in title_l for kw in JAVA_TITLE_KEYWORDS):
        return True

    # Title contains Java + engineer/developer/architect
    if _mentions_java(title_l) and re.search(
        r"\b(developer|engineer|architect|programmer|backend|fullstack|full[\s-]?stack)\b",
        title_l,
    ):
        return True

    if re.search(r"\bspring\s*boot\b", title_l) or re.search(r"\bspring\s*boot\b", desc_l[:500]):
        return True

    # Require at least one Java ecosystem term in title for borderline cases
    if any(term in title_l for term in JAVA_REQUIRED_TERMS):
        return True

    # Avoid collecting generic "Software Engineer" without Java signal
    if _mentions_java(blob[:800]) and any(
        x in title_l for x in ("backend", "software engineer", "sde", "swe")
    ):
        if _mentions_java(desc_l[:1200]):
            return True

    return False


def detect_work_mode(text: str) -> str | None:
    t = text.lower()
    negative_remote = (
        "no remote",
        "not remote",
        "non-remote",
        "non remote",
        "not a remote",
        "unable to offer remote",
        "on-site only",
        "onsite only",
        "in-office only",
        "office based",
        "office-based",
    )
    if any(n in t for n in negative_remote):
        if "hybrid" in t:
            return "hybrid"
        return "onsite"
    if any(x in t for x in ("fully remote", "100% remote", "remote-first", "work from home", "wfh", "work from anywhere")):
        return "remote"
    if "hybrid" in t:
        return "hybrid"
    if any(x in t for x in ("on-site", "onsite", "on site", "in-office", "in office")):
        return "onsite"
    if re.search(r"\bremote\b", t) and not any(n in t for n in negative_remote):
        return "remote"
    return None


def normalize_work_mode(
    text: str,
    *,
    fallback: str | None = None,
    location: str | None = None,
) -> str | None:
    """Resolve work mode from description + optional location hint."""
    blob = f"{text} {location or ''}"
    detected = detect_work_mode(blob)
    if detected:
        return detected
    if location and "remote" in location.lower():
        return "remote"
    return fallback


def detect_visa_sponsorship(text: str) -> bool:
    t = text.lower()
    positive = (
        "visa sponsorship",
        "sponsor visa",
        "h-1b",
        "h1b",
        "h1-b",
        "work permit sponsorship",
        "relocation sponsorship",
        "will sponsor",
        "visa support",
        "work visa",
        "sponsorship available",
        "relocation package",
        "global mobility",
        "immigration support",
        "tier 2 sponsorship",
        "skilled worker visa",
    )
    negative = (
        "no visa sponsorship",
        "cannot sponsor",
        "unable to sponsor",
        "not able to sponsor",
        "sponsorship not available",
    )
    if any(n in t for n in negative):
        return False
    return any(p in t for p in positive)


def detect_experience_level(title: str, description: str = "") -> str | None:
    t = f"{title} {description[:500]}".lower()
    if any(x in t for x in ("principal", "staff engineer", "distinguished")):
        return "principal"
    if any(x in t for x in ("architect",)):
        return "architect"
    if any(x in t for x in ("lead ", " tech lead", "team lead")):
        return "lead"
    if any(x in t for x in ("senior", "sr.", "sr ")):
        return "senior"
    if any(x in t for x in ("junior", "jr.", "jr ")):
        return "junior"
    if any(x in t for x in ("intern", "entry level", "entry-level", "graduate")):
        return "entry"
    if any(x in t for x in ("mid-level", "mid level", "intermediate")):
        return "mid"
    return "mid"


def is_java_related_from_aggregator(title: str, description: str | None = None) -> bool:
    """Relaxed filter for short aggregator snippets (Jooble, Careerjet, Adzuna)."""
    if is_java_related_job(title, description):
        return True
    title_l = (title or "").lower()
    desc_l = (description or "").lower()
    if _is_python_or_ai(title_l, desc_l) or _is_qa_or_pm(title_l, desc_l):
        return True
    if _mentions_java(title_l):
        return True
    if re.search(r"\bpython\b", title_l):
        return True
    if re.search(r"\bspring\b", title_l) and re.search(
        r"\b(developer|engineer|boot|backend)\b", title_l
    ):
        return True
    return False
