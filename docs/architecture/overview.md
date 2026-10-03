# Architecture Overview

## Style

Clean Architecture + Repository Pattern + Dependency Injection (FastAPI `Depends`).

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Next.js)  ·  Chrome Extension (Phase 5)          │
└────────────────────────────┬────────────────────────────────┘
                             │ REST / JWT
┌────────────────────────────▼────────────────────────────────┐
│  API Layer (FastAPI routers + Pydantic schemas)             │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  Application Services (Auth, Ingestion, Dashboard, …)       │
└────────────────────────────┬────────────────────────────────┘
                             │
┌──────────────┬─────────────┼──────────────┬─────────────────┐
│ Repositories │  Domain     │  Collectors  │  AI Engines     │
│              │  (filters)  │  (sources)   │  (Phase 2–3)    │
└──────┬───────┴─────────────┴──────┬───────┴────────┬────────┘
       │                            │                │
       ▼                            ▼                ▼
  PostgreSQL (+ FTS)            Redis/Celery      Qdrant
```

## Async first

- SQLAlchemy async sessions (`asyncpg`)
- `httpx` for outbound HTTP in collectors
- Celery workers for scheduled refresh / expiry

## Auth

- Email + password (bcrypt)
- JWT access + rotating refresh tokens (hashed at rest)
- Google / GitHub OAuth (env-configured)
- Forgot / reset password tokens

## Search

Phase 1: PostgreSQL `ILIKE` + GIN `tsvector` trigger on jobs.  
Phase 2+: semantic search via Qdrant embeddings.

## Ingestion pipeline

1. Connector `fetch()` → `RawJob` list  
2. Java relevance filter  
3. Company upsert  
4. Job upsert by `(source, external_id)`  
5. Content hash for change detection  

## Security notes

- Secrets via `.env` only  
- CORS allowlist  
- No ToS-violating scrapers  
- Official apply links only for applications  
