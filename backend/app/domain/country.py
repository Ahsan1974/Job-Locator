"""Country normalization for job listings."""

import re

from app.core.constants import TARGET_COUNTRIES

# Map common variants to display names used in filters
_COUNTRY_ALIASES: dict[str, str] = {
    "us": "United States",
    "usa": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "great britain": "United Kingdom",
    "england": "United Kingdom",
    "de": "Germany",
    "deutschland": "Germany",
    "ca": "Canada",
    "au": "Australia",
    "in": "India",
    "sg": "Singapore",
    "ae": "United Arab Emirates",
    "uae": "United Arab Emirates",
    "sa": "Saudi Arabia",
    "pk": "Pakistan",
    "nl": "Netherlands",
    "ie": "Ireland",
    "fr": "France",
    "ch": "Switzerland",
    "se": "Sweden",
    "no": "Norway",
    "dk": "Denmark",
    "fi": "Finland",
    "nz": "New Zealand",
    "jp": "Japan",
    "kr": "South Korea",
    "qa": "Qatar",
    "remote": "Remote",
    "worldwide": "Remote",
    "anywhere": "Remote",
    "global": "Remote",
}


def normalize_country(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    key = raw.lower()
    if key in _COUNTRY_ALIASES:
        return _COUNTRY_ALIASES[key]
    if len(raw) <= 3 and key.upper() == raw.upper():
        return _COUNTRY_ALIASES.get(key, raw.upper())
    # "Berlin, Germany" -> Germany
    if "," in raw:
        tail = raw.split(",")[-1].strip()
        return normalize_country(tail) or raw
    # Title-case multi-word countries
    titled = " ".join(part.capitalize() for part in re.split(r"\s+", raw))
    if titled in TARGET_COUNTRIES:
        return titled
    return raw if len(raw) <= 48 else raw[:48]


def country_filter_options() -> list[str]:
    """Preferred dropdown order: Remote + target countries."""
    options = ["Remote"]
    options.extend(sorted(TARGET_COUNTRIES))
    return options
