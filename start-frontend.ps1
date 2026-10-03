# Start Java Career AI frontend (no Docker)
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\frontend"
if (-not (Test-Path "node_modules")) {
  npm install
}
Write-Host "App: http://localhost:3000" -ForegroundColor Cyan
npm run dev
