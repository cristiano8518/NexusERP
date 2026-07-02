# Week 7 Defense Q&A

## 1) Why modular monolith instead of microservices?

- Course scope and team size favor faster iteration.
- Strong transactional consistency is needed between warehouse and finance.
- Domain boundaries are already separated by apps, so migration to microservices is possible later.

## 2) How do you prevent stock inconsistency?

- `transaction.atomic()` wraps stock movement.
- `select_for_update()` locks target product row.
- DB trigger prevents negative quantity at database level.

## 3) How is access control implemented?

- JWT authentication.
- RBAC with custom permissions: admin/manager/employee.
- Manager scope restricted to own department for employees/tasks/finance/reports.

## 4) What performance optimizations were added?

- Composite indexes on high-frequency query paths.
- Redis caching for analytics.
- `select_related` and `prefetch_related` to reduce N+1 queries.

## 5) How do async jobs work?

- Celery worker handles report generation and bulk email.
- API returns fast with `task_id` and `202 Accepted`.
- Redis is broker and result backend.

## 6) How are external integrations secured?

- Webhook HMAC signature validation using `X-Nexus-Timestamp` + `X-Nexus-Signature`.
- External API client has timeout and HTTP/JSON error handling.
- Runtime integration status endpoint for diagnostics.

## 7) What about production readiness?

- Production compose stack with Nginx reverse proxy.
- Secure prod settings (cookies, HTTPS mode, security headers).
- CI for lint + tests + coverage gate; CD workflow for remote deploy.

## 8) What are current known limitations?

- CD requires server secrets and infrastructure provisioning.
- Monitoring stack (Prometheus/Grafana) is not yet bundled by default.
- AI answer quality depends on local Ollama model size and hardware.
