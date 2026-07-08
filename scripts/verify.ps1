# NexusERP verification script
param(
    [switch]$SkipDocker,
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== NexusERP Verification ===" -ForegroundColor Cyan

if (-not $SkipDocker) {
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example"
    }
    docker compose exec -T backend python manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw "migrate failed" }
    docker compose exec -T backend python manage.py check
    if ($LASTEXITCODE -ne 0) { throw "django check failed" }
    docker compose exec -T backend python -m pytest apps/employees/tests/test_rbac_api.py apps/tasks/tests/test_tasks_api.py -q --no-header
    if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
    Write-Host "Backend OK" -ForegroundColor Green
} else {
    Write-Host "Skipped Docker checks" -ForegroundColor Yellow
}

if (-not $SkipFrontend) {
    Push-Location frontend
    if (-not (Test-Path "node_modules")) {
        npm install
    }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "frontend build failed" }
    Pop-Location
    Write-Host "Frontend OK" -ForegroundColor Green
}

Write-Host "=== All checks passed ===" -ForegroundColor Green
