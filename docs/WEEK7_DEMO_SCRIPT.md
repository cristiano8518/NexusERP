# Week 7 Live Demo Script

## Demo Setup Checklist (before presentation)

- `docker compose up --build`
- `docker compose exec backend python manage.py migrate`
- `.\scripts\seed-scale-demo.ps1`
- Open:
  - `http://localhost:3000`
  - `http://localhost:8000/api/docs/`
  - `http://localhost:8000/admin/`

## 0:00 - 1:00 Login and Role Scope

- Login as `admin / admin123`.
- Show dashboard totals and cross-department visibility.
- Logout and login as `scale_manager_01 / manager123`.
- Show the same pages now filtered by manager department.

## 1:00 - 2:30 Task Workflow

- Open `Tasks` and create a task for own department employee.
- As employee user, move task to `in_progress` then `done`.
- As manager, approve task.
- Explain permission boundaries and workflow rules.

## 2:30 - 3:30 Warehouse + Finance Link

- Create warehouse movement (`in` or `out`) from `Warehouse`.
- Show stock quantity update.
- Open `Finance` and show auto-created entry tied to movement.

## 3:30 - 4:30 Analytics and Reports

- Open analytics/reports dashboard.
- Export one CSV report.
- Mention cache benchmark endpoint and Redis acceleration.

## 4:30 - 5:30 Integrations and AI

- Show integration status endpoint (`/api/v1/integrations/status/`).
- Trigger external sync endpoint.
- Open AI assistant page and ask one ERP-related prompt.
- Explain backend proxy and role-scoped context.

## 5:30 - 6:00 Production/CI/CD Summary

- Show GitHub workflow files:
  - CI (`.github/workflows/ci.yml`)
  - CD (`.github/workflows/cd.yml`)
- Explain test coverage gate and deploy pipeline trigger.
