# Start backend + frontend in ONE terminal (no Docker)
# Usage: .\run.ps1 (production UI) or .\run.ps1 -Development (hot reload)
param([switch]$Development)
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
}

function Stop-Port([int]$Port) {
  Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

function Test-PortFree([int]$Port) {
  $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  return -not $listeners
}

function Get-FreePort([int]$Preferred, [int[]]$Fallbacks) {
  Stop-Port $Preferred
  Start-Sleep -Milliseconds 500
  if (Test-PortFree $Preferred) { return $Preferred }
  foreach ($p in $Fallbacks) {
    Stop-Port $p
    Start-Sleep -Milliseconds 300
    if (Test-PortFree $p) { return $p }
  }
  throw "No free port found (tried $Preferred and $($Fallbacks -join ', '))"
}

$ApiPort = Get-FreePort 8000 @(8080, 8888, 5000)
$WebPort = Get-FreePort 3000 @(3001, 3002, 3003)

$env:API_PORT = "$ApiPort"
$env:WEB_PORT = "$WebPort"
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:${ApiPort}/api/v1"

# Keep .env in sync so Next.js picks up the correct API port
$envFile = Join-Path $Root ".env"
$apiLine = "NEXT_PUBLIC_API_URL=http://127.0.0.1:${ApiPort}/api/v1"
if (Test-Path $envFile) {
  $content = Get-Content $envFile -Raw
  if ($content -match "NEXT_PUBLIC_API_URL=") {
    $content = $content -replace "NEXT_PUBLIC_API_URL=.*", $apiLine
  } else {
    $content += "`n$apiLine`n"
  }
  Set-Content -Path $envFile -Value $content.TrimEnd() -NoNewline
  Add-Content -Path $envFile -Value ""
}

Write-Host ""
Write-Host "=== Job Hunter ===" -ForegroundColor Cyan
Write-Host "API:  http://127.0.0.1:$ApiPort/docs"
Write-Host "App:  http://localhost:$WebPort"
Write-Host "No login required - opens straight to dashboard." -ForegroundColor Green
Write-Host "Tip: Add JOOBLE_API_KEY + ADZUNA keys in .env for thousands more jobs." -ForegroundColor Yellow
Write-Host ""

$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
$VenvPip = Join-Path $BackendDir ".venv\Scripts\pip.exe"

if (-not (Test-Path $VenvPython)) {
  Set-Location $BackendDir
  python -m venv .venv
  & $VenvPip install -r requirements.txt
}

if (-not (Test-Path (Join-Path $Root "data\java_career_ai.db"))) {
  Set-Location $BackendDir
  & $VenvPython -m scripts.seed
  Set-Location $Root
}

Set-Location $Root
if (-not (Test-Path "node_modules\concurrently")) {
  npm install
}
if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
  npm install --prefix frontend
}

if ($Development) {
  $ApiCmd = "cd backend && .venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $ApiPort"
  $WebCmd = "cd frontend && npm run dev -- --port $WebPort"
  Write-Host "Mode: development (hot reload)" -ForegroundColor Yellow
} else {
  if (-not (Test-Path (Join-Path $FrontendDir ".next\BUILD_ID"))) {
    Write-Host "Creating the production frontend build (first run only)..." -ForegroundColor Yellow
    npm run build --prefix frontend
  }
  $StandaloneDir = Join-Path $FrontendDir ".next\standalone"
  $StandalonePublic = Join-Path $StandaloneDir "public"
  $StandaloneStatic = Join-Path $StandaloneDir ".next\static"
  New-Item -ItemType Directory -Force -Path $StandalonePublic | Out-Null
  New-Item -ItemType Directory -Force -Path $StandaloneStatic | Out-Null
  Copy-Item (Join-Path $FrontendDir "public\*") $StandalonePublic -Recurse -Force
  Copy-Item (Join-Path $FrontendDir ".next\static\*") $StandaloneStatic -Recurse -Force
  $env:PORT = "$WebPort"
  $env:HOSTNAME = "0.0.0.0"
  $ApiCmd = "cd backend && .venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port $ApiPort"
  $WebCmd = "cd frontend && node .next\standalone\server.js"
  Write-Host "Mode: production (no development error overlay)" -ForegroundColor Green
}

npx concurrently -k -n API,WEB -c blue,green $ApiCmd $WebCmd
