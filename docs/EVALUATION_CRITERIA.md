# Evaluation Criteria Mapping

## Week 1: Architecture and Containerization

Implemented:

- Approved project document: `docs/TECHNICAL_SPEC.md`.
- Modular monolith/service-oriented architecture.
- Dockerized stack:
  - `docker-compose.yml`
  - `backend/Dockerfile`
  - `frontend/Dockerfile`
  - `docker-compose.prod.yml`
  - `nginx/nginx.conf`

Verification:

```powershell
docker compose up --build
```

Open:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/api/v1/health/`
- Swagger: `http://localhost:8000/api/docs/`

## Week 2: Complex Database Queries and Caching

Implemented:

- Composite indexes:
  - `tasks/migrations/0003_task_performance_indexes.py`
  - `finance/migrations/0002_finance_performance_indexes.py`
  - `warehouse/migrations/0003_warehouse_performance_indexes.py`
- PostgreSQL trigger:
  - `warehouse/migrations/0004_product_quantity_trigger.py`
  - Prevents negative product quantity at database level.
- N+1 prevention through `select_related()` and `prefetch_related()`.
- Transactional stock movement with `transaction.atomic()` and `select_for_update()`.
- Redis-backed analytics cache in `apps/analytics/services.py`.
- Cache benchmark endpoint:
  - `GET /api/v1/analytics/cache-benchmark/`

Verification:

```powershell
docker compose exec backend python manage.py migrate
```

Then call:

```text
GET http://localhost:8000/api/v1/analytics/cache-benchmark/
```

The response includes `uncached_ms`, `cached_ms`, `speedup_ratio`, and `same_payload`.

## Week 3: Background Jobs

Implemented with Celery and Redis:

- Async CSV report generation:
  - Task: `reports.generate_csv`
  - Endpoint: `POST /api/v1/reports/async/`
  - Payload: `{ "report_type": "finance" }`
- Bulk email:
  - Task: `notifications.bulk_email`
  - Endpoint: `POST /api/v1/notifications/bulk-email/`
  - Payload: `{ "subject": "...", "message": "...", "role": "employee" }`

Verification:

```powershell
docker compose logs celery_worker --tail 100
```

Both endpoints return `202 Accepted` with a `task_id`, proving the request thread is not blocked.

## Week 4: External Systems Integration

Implemented:

- External employee sync client:
  - `apps/integrations/services.py`
  - Supports `ODOO_EMPLOYEES_URL` or mock mode.
  - Handles timeout and external 500-style failures.
- Async external sync:
  - Task: `integrations.sync_external_employees`
  - Endpoint: `POST /api/v1/integrations/external-employees/`
- Synchronous external fetch:
  - Endpoint: `GET /api/v1/integrations/external-employees/`
- Secure webhook endpoint:
  - `POST /api/v1/integrations/webhooks/external/`
  - Header: `X-Nexus-Signature: <EXTERNAL_WEBHOOK_SECRET>`

Verification:

```text
GET  /api/v1/integrations/status/
GET  /api/v1/integrations/external-employees/
POST /api/v1/integrations/external-employees/
POST /api/v1/integrations/webhooks/external/
```

Environment variables:

```env
ODOO_EMPLOYEES_URL=
EXTERNAL_API_TIMEOUT_SECONDS=5
EXTERNAL_WEBHOOK_SECRET=dev-webhook-secret
```
