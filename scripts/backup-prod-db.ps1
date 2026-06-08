# Backup NexusERP production PostgreSQL database from Docker
Set-Location $PSScriptRoot\..

if (!(Test-Path ".env.production")) {
  Write-Host "Missing .env.production. Copy .env.production.example first." -ForegroundColor Red
  exit 1
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = "backups"
$file = "$backupDir\nexuserp-prod-$timestamp.sql"

if (!(Test-Path $backupDir)) {
  New-Item -ItemType Directory -Path $backupDir | Out-Null
}

Write-Host "Creating production backup: $file" -ForegroundColor Cyan
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > $file

Write-Host "Backup complete: $file" -ForegroundColor Green
