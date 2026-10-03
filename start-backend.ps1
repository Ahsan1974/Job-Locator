# Start Java Career AI backend (no Docker)
# Run from project root: .\start-backend.ps1
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location "$Root\backend"

if (-not (Test-Path ".venv")) {
  Write-Host "No backend venv found. Run .\setup.ps1 first." -ForegroundColor Yellow
  python -m venv .venv
  & ".\.venv\Scripts\Activate.ps1"
  pip install -r requirements.txt
  python -m scripts.seed
} else {
  & ".\.venv\Scripts\Activate.ps1"
}

if (-not (Test-Path "..\data\java_career_ai.db")) {
  python -m scripts.seed
}

Write-Host "API: http://localhost:8000/docs" -ForegroundColor Cyan
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
