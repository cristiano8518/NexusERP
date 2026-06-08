# NexusERP local healthcheck
Set-Location $PSScriptRoot\..

Write-Host "Docker services:" -ForegroundColor Cyan
docker compose ps

Write-Host "`nBackend health:" -ForegroundColor Cyan
try {
  Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health/" -UseBasicParsing | Select-Object -ExpandProperty Content
} catch {
  Write-Host "Backend health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nFrontend:" -ForegroundColor Cyan
try {
  $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing
  Write-Host "Frontend OK: HTTP $($response.StatusCode)" -ForegroundColor Green
} catch {
  Write-Host "Frontend check failed: $($_.Exception.Message)" -ForegroundColor Red
}
