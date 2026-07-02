# NexusERP Improvement Plan

## Current Gaps Found

1. Docker startup command could hide migration failures because the optional
   `token_blacklist` migration was not grouped correctly.
2. Some report summary calculations used Python loops instead of database
   filters.
3. Warehouse frontend expected validation errors only in one response shape.
4. Finance and profile pages did not show clear API load failures.
5. External integration client needed clearer HTTP/JSON error handling.
6. The project needs a stronger next-step roadmap after the course criteria.

## Fixes Implemented

- Docker command now only ignores the optional `token_blacklist` migration, not
  the main migration pipeline.
- Celery Beat now uses the same `DJANGO_SETTINGS_MODULE` and result backend as
  the worker.
- Report summary now calculates overdue tasks and low stock products with
  database queries.
- Warehouse operation errors now support DRF field errors, custom detail errors
  and legacy error shapes.
- Finance page now shows a visible load error instead of silently showing empty
  data.
- Profile page now handles failed profile loading cleanly.
- External API integration now handles HTTP errors, URL/timeouts and invalid
  JSON separately.
- Webhook endpoint stores the last received event in cache for debugging/demo.

## Full Next Plan

### Priority 1: Stability

- Add automated backend tests for task workflow, warehouse stock movement and
  finance CRUD.
- Add frontend smoke tests for login, dashboard, tasks and finance.
- Add a single verification script that runs migrations, Django checks and
  frontend build.

### Priority 2: Product Logic

- Add audit logs for finance and warehouse edit/delete actions.
- Add notification preferences per user.
- Add task attachments and document uploads.
- Add finance budgets and category limits.

### Priority 3: Integrations

- Replace mock Odoo sync with a real configured API URL.
- Add Telegram notifications.
- Add payment webhook examples.
- Add retry policy and dead-letter style logging for failed background jobs.

### Priority 4: Production Readiness

- Add HTTPS-ready Nginx template.
- Add database backup restore script.
- Add CI workflow for backend checks and frontend build.
- Add monitoring endpoints and structured logs.

## Verification Commands

Run from project root:

```powershell
cd C:\Users\user\NexusERP
docker compose up --build
```

In another terminal:

```powershell
cd C:\Users\user\NexusERP
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py check
```

Frontend build:

```powershell
cd C:\Users\user\NexusERP\frontend
npm run build
```

Important API checks:

```text
GET  /api/v1/health/
GET  /api/v1/analytics/cache-benchmark/
POST /api/v1/reports/async/
POST /api/v1/notifications/bulk-email/
GET  /api/v1/integrations/external-employees/
POST /api/v1/integrations/webhooks/external/
```
