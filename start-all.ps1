# Start both backend and frontend (no Docker)
# Prefer: .\run.ps1  (single terminal)
$root = $PSScriptRoot
Write-Host "Tip: use .\run.ps1 for a single terminal." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$root\start-backend.ps1"
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-File", "$root\start-frontend.ps1"
Write-Host "Frontend: http://localhost:3000"
Write-Host "API docs: http://localhost:8000/docs"
Write-Host "Login: demo@javacareer.ai / DemoPass123!"