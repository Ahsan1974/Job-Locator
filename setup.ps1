# One-time setup (run from project root)
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Write-Host "=== Java Career AI Setup ===" -ForegroundColor Cyan

if (-not (Test-Path "$Root\.env")) {
  Copy-Item "$Root\.env.example" "$Root\.env"
  Write-Host "Created .env from .env.example"
}

$BackendDir = Join-Path $Root "backend"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
$VenvPip = Join-Path $BackendDir ".venv\Scripts\pip.exe"

Set-Location $BackendDir
if (-not (Test-Path ".venv")) {
  Write-Host "Creating Python virtual environment in backend\.venv ..."
  python -m venv .venv
}

& $VenvPython -m pip install --upgrade pip
& $VenvPip install -r requirements.txt
& $VenvPython -m scripts.seed

Set-Location (Join-Path $Root "frontend")
if (-not (Test-Path "node_modules")) {
  Write-Host "Installing frontend dependencies ..."
  npm install
}

Set-Location $Root
if (-not (Test-Path "node_modules")) {
  npm install
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "Run the app with:  .\run.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Login: demo@javacareer.ai / DemoPass123!" -ForegroundColor Yellow
