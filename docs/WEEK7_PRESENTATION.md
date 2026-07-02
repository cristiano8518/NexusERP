# Week 7 Presentation Plan

## 1) Problem and Goal (1 minute)

- Companies need one place to manage people, tasks, inventory and finance.
- NexusERP goal: one modular platform with clear role logic and real business workflow.

## 2) Architecture (2 minutes)

- Frontend: Next.js 15 + TypeScript + Tailwind.
- Backend: Django REST Framework (modular monolith by domain apps).
- Data and infra: PostgreSQL + Redis + Celery + Docker Compose.
- Production ingress: Nginx (`/`, `/api/`, `/admin/`).

## 3) Core Business Logic (2 minutes)

- Role model: admin, manager, employee.
- Manager sees only own department, admin sees all departments.
- Task workflow:
  - `assigned -> in_progress -> done -> approved/rejected`
- Warehouse stock movement:
  - atomic transactions
  - row lock (`select_for_update`)
  - auto finance entries.

## 4) Performance and Reliability (1.5 minutes)

- Composite DB indexes for hot filters.
- Redis cache for analytics and benchmark endpoint.
- Background jobs for reports and bulk email (Celery).
- Error handling for external integration and AI proxy.

## 5) Security and Production Readiness (1.5 minutes)

- JWT auth and RBAC permissions.
- Security log events.
- Webhook signature validation.
- API throttling (global + auth endpoints).
- CI with lint, tests, and coverage gate (>=40%).
- CD workflow for server deploy over SSH.

## 6) Demo Highlights (2 minutes)

- Login as admin and manager, show scope difference.
- Show task lifecycle and approval flow.
- Show warehouse movement and finance auto-entry.
- Show analytics/reports and AI assistant response.

## 7) Conclusion (30 seconds)

- Course requirements from Week 1 to Week 7 are implemented.
- Project is ready for extension with monitoring and cloud deployment.
