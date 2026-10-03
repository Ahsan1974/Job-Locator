# Developer Documentation

## Conventions

- Type hints everywhere in Python
- Pydantic v2 schemas at the API boundary
- Repositories own SQL; services own business rules
- Collectors never write to the DB directly — return `RawJob`
- Frontend: App Router, client components for interactive views, TanStack Query for server state

## Running tests

```bash
cd backend
pytest -q
```

## Adding a job source

1. Create `backend/app/collectors/mysource.py` implementing `JobSourceConnector`
2. Use only official APIs or permitted feeds
3. Apply `is_java_related_job()` before returning rows
4. Register in `get_connectors()` inside `ingestion_service.py`
5. Document legal basis in `job_sources/__init__.py`

## Database migrations

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Local demo data

```bash
python -m scripts.seed
```

## Phase roadmap hooks

| Module | Entry |
|--------|-------|
| Resume parse | `resume_parser.ResumeParser` |
| Match | `resume_match_engine.ResumeMatchEngine` |
| Recommend | `recommendation_engine.RecommendationEngine` |
| Salary | `salary_estimator.SalaryEstimator` |
| Skill gap | `skill_gap_engine.SkillGapEngine` |
| Company intel | `company_intelligence.CompanyIntelligenceService` |
| Analytics | `analytics.AnalyticsService` |

Wire these into FastAPI routers in later phases without changing the Phase 1 job/auth contracts.
