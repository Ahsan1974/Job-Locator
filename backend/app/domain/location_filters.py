"""Location-based filters for job queries."""

from sqlalchemy import Select, and_, not_, or_

from app.models.job import Job

INDIA_COUNTRY_VALUES = ("India", "IN", "IND")

INDIA_LOCATION_MARKERS = (
    "%india%",
    "%telangana%",
    "%maharashtra%",
    "%karnataka%",
    "%tamil nadu%",
    "%bangalore%",
    "%bengaluru%",
    "%mumbai%",
    "%delhi%",
    "%pune%",
    "%chennai%",
    "%kolkata%",
    "%gurgaon%",
    "%noida%",
    "%andhra pradesh%",
    "%kerala%",
)


def _ilike_present(column, pattern: str):
    """True only when the column has text that matches. NULL stays false, not unknown."""
    return and_(column.is_not(None), column.ilike(pattern))


def is_india_job_filter():
    """SQLAlchemy clause matching Indian listings."""
    country_match = or_(
        Job.country.in_(INDIA_COUNTRY_VALUES),
        _ilike_present(Job.country, "%India%"),
    )
    location_match = or_(
        *[_ilike_present(Job.location_raw, marker) for marker in INDIA_LOCATION_MARKERS],
        *[_ilike_present(Job.city, marker) for marker in INDIA_LOCATION_MARKERS],
    )
    pakistan_exception = or_(
        _ilike_present(Job.country, "%Pakistan%"),
        _ilike_present(Job.location_raw, "%Pakistan%"),
        Job.source.in_(("pakistan", "indeed_pk", "rozee", "jooble_pk", "mustakbil")),
    )
    return or_(country_match, and_(location_match, not_(pakistan_exception)))


def apply_exclude_india(stmt: Select) -> Select:
    return stmt.where(~is_india_job_filter())
