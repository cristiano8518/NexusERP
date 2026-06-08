# NexusERP Technical Specification

## Project Topic

NexusERP is a corporate ERP platform for managing internal business processes:
employees, task workflow, warehouse stock, finance, analytics, reports, notifications,
and external integrations.

## Business Processes

- Manager assigns tasks to employees.
- Employee works through `assigned -> in_progress -> done`.
- Manager approves or rejects completed work.
- Warehouse stock movements update product balance and can automatically create finance entries.
- Finance tracks income, expense, categories, cashflow and report exports.
- Notifications and background jobs keep long operations outside the request thread.
- External APIs/webhooks allow data exchange with systems such as Odoo or payment gateways.

## Architecture Decision

The project uses a modular monolith with service-oriented boundaries.

Why not microservices at this stage:

- The project is educational/portfolio sized.
- Strong transactional consistency is required between warehouse and finance.
- One deployable backend is simpler to debug and demonstrate.

Service-oriented boundaries inside the monolith:

- `accounts` - authentication, users, roles, security logs.
- `employees` - departments, positions, employee HR profiles.
- `tasks` - workflow, comments, activity history.
- `warehouse` - products, stock movements, low stock events.
- `finance` - income/expense ledger.
- `analytics` - cached KPI aggregation.
- `reports` - synchronous CSV and asynchronous CSV generation.
- `notifications` - notifications, email and bulk email background jobs.
- `integrations` - external API clients and webhook entry points.

## Infrastructure

- Backend: Django REST Framework.
- Frontend: Next.js, TypeScript, TailwindCSS.
- Database: PostgreSQL.
- Cache and broker: Redis.
- Background jobs: Celery worker and Celery Beat.
- Containerization: Docker Compose.
- Production-like ingress: Nginx reverse proxy.

## Data Integrity

- Warehouse movement creation uses `transaction.atomic()` and row locking with
  `select_for_update()` so concurrent stock updates do not corrupt quantity.
- Finance and warehouse can be committed as a single transaction.
- Composite database indexes cover high-traffic filters such as task status,
  assignee/status, finance type/date, finance category/date and stock movement history.

## Security

- JWT authentication.
- Role-based access control: admin, manager, employee.
- Security logs for login/register/token refresh events.
- Webhook signature validation through `X-Nexus-Signature`.
- Production settings support secure cookies and HTTPS mode.

## Evaluation Deliverables

- Technical assignment: this document.
- GitHub-ready project structure with `.gitignore`, README and Docker configuration.
- Dockerized local stack with PostgreSQL, Redis, backend, Celery and frontend.
- Optimized relational schema and cache benchmark endpoint.
- Background jobs for report generation and bulk email.
- External API sync and webhook processing endpoints.
