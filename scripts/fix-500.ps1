# Fix API 500 errors — migrations + restart
Set-Location $PSScriptRoot\..

Write-Host "Migrating database..." -ForegroundColor Cyan
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py migrate django_celery_beat --noinput 2>$null
docker compose exec backend python manage.py migrate django_celery_results --noinput 2>$null

Write-Host "Rebuilding backend..." -ForegroundColor Cyan
docker compose up --build -d backend

Write-Host "Backend logs (last 40 lines):" -ForegroundColor Yellow
docker compose logs backend --tail 40

Write-Host "`nTest: http://localhost:8000/api/v1/health/" -ForegroundColor Green
