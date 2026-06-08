# NexusERP production-like deploy helper
Set-Location $PSScriptRoot\..

if (!(Test-Path ".env.production")) {
  Write-Host "Missing .env.production. Copy .env.production.example first." -ForegroundColor Red
  Write-Host "copy .env.production.example .env.production"
  exit 1
}

Write-Host "Building and starting production stack..." -ForegroundColor Cyan
docker compose -f docker-compose.prod.yml --env-file .env.production up --build -d

Write-Host "`nRunning migrations..." -ForegroundColor Cyan
docker compose -f docker-compose.prod.yml --env-file .env.production exec backend python manage.py migrate --noinput

Write-Host "`nCollecting static..." -ForegroundColor Cyan
docker compose -f docker-compose.prod.yml --env-file .env.production exec backend python manage.py collectstatic --noinput

Write-Host "`nStatus:" -ForegroundColor Green
docker compose -f docker-compose.prod.yml --env-file .env.production ps

Write-Host "`nOpen: http://localhost" -ForegroundColor Green
