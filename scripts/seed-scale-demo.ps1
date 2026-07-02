# Create realistic large demo data for dashboards, analytics and reports
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "Running migrations..." -ForegroundColor Cyan
docker compose exec backend python manage.py migrate
if ($LASTEXITCODE -ne 0) { throw "Migration failed." }

Write-Host "`nSeeding large realistic demo data..." -ForegroundColor Cyan
docker compose exec backend python manage.py seed_scale_demo --reset-scale --employees 48 --tasks 240 --finance 220 --movements 160
if ($LASTEXITCODE -ne 0) { throw "Scale demo seed failed." }

Write-Host "`nDone. Open http://localhost:3000/dashboard" -ForegroundColor Green
Write-Host "Demo logins:"
Write-Host "  admin / admin123"
Write-Host "  manager / manager123"
Write-Host "  scale_manager_01 / manager123"
Write-Host "  scale_employee_001 / employee123"
