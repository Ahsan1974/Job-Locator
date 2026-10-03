# Linux Setup (No Docker)

## Prerequisites

- Python 3.13+
- Node.js 20+

## Start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.seed
uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

SQLite database is created automatically under `data/java_career_ai.db`.
