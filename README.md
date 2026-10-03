# Job Hunter

AI-powered software career platform with a Java focus plus Python, AI, QA,
project management, and freelance work.

Runs **fully locally with SQLite** — **no Docker, Redis, Postgres, or Qdrant required**.

---

## Quick start (Windows) — one command

```powershell
cd "D:\Job Locator"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\setup.ps1
.\run.ps1
```

This starts the backend and the production frontend in one terminal, frees ports
if busy, and fetches live jobs on startup. Use `.\run.ps1 -Development` only
when you need hot reload and the Next.js development overlay.

After startup, click **Refresh** in the top bar or wait ~30s for automatic live job import.

No login is required in local mode.

---

## Quick start (Linux / macOS)

```bash
chmod +x start-backend.sh
./start-backend.sh
# other terminal:
cd frontend && npm install && npm run dev
```

---

## What is included (all phases)

| Area | Features |
|------|----------|
| Auth | Email register/login, JWT + refresh, forgot password, Google/GitHub OAuth hooks |
| Jobs | Aggregation (RemoteOK, Remotive, Arbeitnow, USAJobs), search, filters, details |
| Resume | PDF/DOCX upload, parsing, primary resume, live side-by-side compare |
| AI Match | Skill / experience / education / tech / ATS scores (0–100) |
| Recommendations | Recompute ranking + high/medium/low priority |
| Salary | Estimator + tech demand insights |
| Skill gap | Missing skills, learning hours, courses, projects |
| Cover letter / Optimizer / Interview prep | Template engine; OpenAI optional |
| Applications | Tracker with status workflow |
| Alerts & notifications | CRUD alerts + in-app notifications |
| Analytics | Charts for apps, countries, tech demand, match distribution |
| Chrome extension | Match score popup scaffold |
| Scheduler | APScheduler in-process (replaces Celery) |

---

## Stack

- **Backend:** Python 3.13 · FastAPI · SQLAlchemy · SQLite · APScheduler
- **Frontend:** Next.js 15 · React · TypeScript · Tailwind · TanStack Query · Recharts
- **Optional:** `OPENAI_API_KEY` for richer cover letters / resume rewrites

---

## Data location

- Database: `data/java_career_ai.db`
- Uploads: `data/uploads/`

---

## Docs

- [Architecture](docs/architecture/overview.md)
- [ER diagram](docs/architecture/er-diagram.md)
- [Windows setup](docs/setup/windows.md)
- [Linux setup](docs/setup/linux.md)
- [Developer guide](docs/developer.md)

---

## Legal note on job sources

Only official / public APIs are enabled. Boards that require ToS-restricted scraping remain stubs until a permitted API/partner feed is available.
