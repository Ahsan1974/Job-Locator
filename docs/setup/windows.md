# Windows Setup (No Docker)

## First-time setup

```powershell
cd "D:\Job Locator"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\setup.ps1
```

This creates `backend\.venv`, installs Python + npm packages, and seeds demo data.

## Run the app

```powershell
.\start-all.ps1
```

- App: http://localhost:3000
- API: http://localhost:8000/docs
- Login: `demo@javacareer.ai` / `DemoPass123!`

## Manual commands (if you prefer)

**Terminal 1 — Backend**

```powershell
cd "D:\Job Locator\backend"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m scripts.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — Frontend**

```powershell
cd "D:\Job Locator\frontend"
npm install
npm run dev
```

## Common mistake

Do **not** run `pip install -r requirements.txt` from the project root unless you use `backend\requirements.txt`. The correct venv path is `backend\.venv`, not `D:\Job Locator\.venv`.
