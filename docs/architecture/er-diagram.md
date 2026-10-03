# Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ refresh_tokens : has
    users ||--o{ resumes : owns
    users ||--o{ applications : tracks
    users ||--o{ saved_jobs : bookmarks
    users ||--o{ alerts : configures
    users ||--o{ notifications : receives

    companies ||--o{ jobs : posts
    companies ||--o{ recruiters : employs
    recruiters ||--o{ jobs : owns

    jobs ||--o{ job_skills : requires
    skills ||--o{ job_skills : tagged

    resumes ||--o{ resume_embeddings : vectors
    jobs ||--o{ applications : receives
    jobs ||--o{ saved_jobs : saved

    users {
        uuid id PK
        string email UK
        string hashed_password
        string auth_provider
        bool is_active
    }

    companies {
        uuid id PK
        string name UK
        string slug UK
        bool offers_visa_sponsorship
    }

    jobs {
        uuid id PK
        uuid company_id FK
        string title
        string source
        string external_id
        string work_mode
        bool visa_sponsorship
        numeric salary_min
        numeric salary_max
        tsvector search_vector
    }

    resumes {
        uuid id PK
        uuid user_id FK
        text raw_text
        text parsed_json
        bool is_primary
    }

    applications {
        uuid id PK
        uuid user_id FK
        uuid job_id FK
        string status
    }
```

## Core tables (Phase 1+)

| Table | Purpose |
|-------|---------|
| `users` | Accounts & preferences |
| `refresh_tokens` | Secure sessions |
| `companies` | Employer profiles |
| `recruiters` | Hiring contacts |
| `jobs` | Normalized postings + FTS |
| `job_skills` | Job ↔ skill M2M |
| `skills` / `technologies` | Taxonomies |
| `resumes` / `resume_embeddings` | Phase 2 |
| `applications` / `saved_jobs` | Tracking |
| `alerts` / `notifications` | Phase 4 |
