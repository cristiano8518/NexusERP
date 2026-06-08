# Backup NexusERP PostgreSQL database from Docker
Set-Location $PSScriptRoot\..

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = "backups"
$file = "$backupDir\nexuserp-$timestamp.sql"

if (!(Test-Path $backupDir)) {
  New-Item -ItemType Directory -Path $backupDir | Out-Null
}

Write-Host "Creating backup: $file" -ForegroundColor Cyan
docker compose exec -T postgres pg_dump -U nexuserp nexuserp > $file

Write-Host "Backup complete: $file" -ForegroundColor Green
