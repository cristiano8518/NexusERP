# NexusERP — парольдерді қалпына келтіру (кіру жұмыс істемесе)
Set-Location $PSScriptRoot\..

Write-Host "1. Checking Docker..." -ForegroundColor Cyan
docker compose ps

Write-Host "`n2. Running migrations..." -ForegroundColor Cyan
docker compose exec backend python manage.py migrate --noinput

Write-Host "`n3. Creating demo users + data..." -ForegroundColor Cyan
docker compose exec backend python manage.py seed_demo

Write-Host "`n4. Resetting passwords..." -ForegroundColor Cyan
docker compose exec backend python manage.py reset_demo_passwords

Write-Host "`n=== LOGIN ===" -ForegroundColor Green
Write-Host "  Site:  http://localhost:3000/login"
Write-Host "  Admin:    admin / admin123"
Write-Host "  Manager:  manager / manager123"
Write-Host "  Employee: employee / employee123"
