# NexusERP

NexusERP is a full-stack corporate ERP platform for running a company's internal operations from one place: people and org structure, task workflows, warehouse stock, finance, analytics and reporting. It pairs a Django REST API (JWT auth, role-based access control, Celery background jobs) with a Next.js + TypeScript dashboard, and ships with Docker Compose stacks for development and a production-like deployment behind Nginx. It also includes a local AI assistant powered by Ollama that answers questions using ERP data the current user is allowed to see.

> Kazakh-language documentation: [docs/README.kk.md](docs/README.kk.md)

## Key features

- **Authentication & security** – JWT access/refresh tokens with blacklist, registration, security and audit logs, DRF rate limiting for anonymous users, logged-in users, login and registration.
- **Role-based access control** – `admin`, `manager` and `employee` roles with a permission registry and data scopes (all / department / own); managers see only their department.
- **HR** – departments, positions, org structure view, employee profiles, task summaries and salary visibility rules.
- **Tasks** – task workflow with status timeline, comments, attachments and activity history.
- **Warehouse** – products, stock levels, incoming/outgoing movements, product history, automatic finance entries.
- **Finance** – income/expense records, category breakdown and cash flow.
- **Analytics & reports** – dashboard aggregates (Redis-cached), CSV export, asynchronous report generation, printable views.
- **Notifications** – notification center with unread counters and Celery-based email delivery.
- **Integrations** – external employee API sync with timeout/error handling and HMAC-signed incoming webhooks.
- **AI assistant** – role-aware chat endpoint that builds ERP context and queries a local Ollama model.
- **API docs** – OpenAPI schema with Swagger UI and ReDoc; Jazzmin-themed Django admin.
- **CI/CD** – GitHub Actions for lint (ruff), tests with a coverage gate, frontend build, and an SSH deploy workflow.

## Tech stack

| Layer | Technologies |
|-------|--------------|
| Backend | Python 3.12, Django 5.1, Django REST Framework, SimpleJWT, drf-spectacular, django-environ |
| Background jobs | Celery, django-celery-beat, django-celery-results |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, Axios, lucide-react |
| Database / cache | PostgreSQL 16, Redis 7 |
| Infrastructure | Docker, Docker Compose, Nginx, Gunicorn, WhiteNoise |
| Quality | pytest, pytest-django, pytest-cov, ruff, GitHub Actions |
| AI | Ollama (default model `llama3.1:8b`) |

## Project structure

```
NexusERP/
├── backend/                  # Django API
│   ├── apps/                 # Domain apps
│   │   ├── accounts/         #   users, auth, roles, security/audit logs, demo seeders
│   │   ├── employees/        #   departments, positions, HR profiles
│   │   ├── tasks/            #   task workflow, comments, attachments
│   │   ├── warehouse/        #   products and stock movements
│   │   ├── finance/          #   income / expense records
│   │   ├── analytics/        #   dashboard aggregates
│   │   ├── reports/          #   CSV / async report export
│   │   ├── notifications/    #   notification center, email jobs
│   │   ├── integrations/     #   external API sync, webhooks
│   │   └── ai/               #   Ollama assistant
│   ├── common/               # Shared code: RBAC, permissions, middleware, throttling, health check
│   ├── config/               # Settings (base/dev/prod), URLs, Celery, Jazzmin
│   └── requirements/         # base.txt, dev.txt
├── frontend/                 # Next.js app (src/app, components, contexts, lib)
├── nginx/                    # Reverse proxy config for the production stack
├── scripts/                  # PowerShell helpers (deploy, backup, seed, healthcheck, verify)
├── docs/                     # Technical spec, troubleshooting, course/defense material
├── docker-compose.yml        # Development stack
├── docker-compose.prod.yml   # Production-like stack
└── .github/workflows/        # CI and CD pipelines
```

## Getting started

### Prerequisites

- Docker and Docker Compose (recommended), **or**
- Python 3.12, Node.js 20, PostgreSQL 16 and Redis 7 for a local setup
- Optional: [Ollama](https://ollama.com) for the AI assistant

### Run with Docker (development)

```bash
cp .env.example .env          # Windows: copy .env.example .env
# edit .env and set SECRET_KEY
docker compose up --build
```

The stack starts `postgres`, `redis`, `backend` (runs migrations and collectstatic, then Gunicorn with reload), `celery_worker`, `celery_beat` and `frontend` (Next.js dev server).

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| REST API | http://localhost:8000/api/v1/ |
| Swagger UI | http://localhost:8000/api/docs/ |
| ReDoc | http://localhost:8000/api/redoc/ |
| Django admin | http://localhost:8000/admin/ |
| Health check | http://localhost:8000/api/v1/health/ |

Create an admin account and (optionally) demo data:

```bash
docker compose exec backend python manage.py createsuperuser

# small demo dataset
docker compose exec backend python manage.py seed_demo

# larger, realistic dataset for dashboards and reports
docker compose exec backend python manage.py seed_scale_demo --reset-scale \
  --employees 48 --tasks 240 --finance 220 --movements 160
```

The demo seeders create sample accounts (for example `admin`, `manager`, `employee`); see `backend/apps/accounts/management/commands/` for details. They are for local demos only.

### Run locally without Docker

Start PostgreSQL and Redis (for example `docker compose up -d postgres redis`), then:

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements/dev.txt
export DJANGO_SETTINGS_MODULE=config.settings.dev
# The settings read ../.env; point the hosts at localhost, e.g.
# DATABASE_URL=postgres://nexuserp:nexuserp_secret@localhost:5432/nexuserp
# REDIS_URL=redis://localhost:6379/0
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# Celery (separate terminals, from backend/)
celery -A config worker -l info
celery -A config beat -l info

# Frontend
cd frontend
npm install
npm run dev                      # http://localhost:3000
```

### Production-like deployment

The production stack serves everything on port 80 through Nginx (`/` → Next.js, `/api/` and `/admin/` → Django, `/static/` and `/media/` → Nginx).

```bash
cp .env.production.example .env.production
# set SECRET_KEY, POSTGRES_PASSWORD, DATABASE_URL, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, SMTP settings
docker compose -f docker-compose.prod.yml --env-file .env.production up --build -d
```

On Windows, `scripts/prod-deploy.ps1` wraps these steps, and `scripts/backup-db.ps1` / `scripts/backup-prod-db.ps1` dump the database into `backups/`.

### AI assistant (optional)

```bash
ollama serve
ollama pull llama3.1:8b
```

The backend calls Ollama at `OLLAMA_BASE_URL` (default `http://host.docker.internal:11434`; use `http://localhost:11434` when the backend runs outside Docker).

## Testing and linting

```bash
cd backend
ruff check .
pytest --cov=apps --cov-report=term-missing

cd ../frontend
npm run build
```

CI (`.github/workflows/ci.yml`) runs ruff, migrations and pytest against PostgreSQL/Redis services with a coverage threshold, and builds the frontend.

## Environment variables

See [`.env.example`](.env.example) (development) and [`.env.production.example`](.env.production.example) (production) for the full list with placeholder values.

| Group | Variables |
|-------|-----------|
| General | `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `USE_HTTPS` |
| Database | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `DATABASE_URL` |
| Redis / Celery | `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` |
| Auth / rate limits | `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`, `JWT_REFRESH_TOKEN_LIFETIME_DAYS`, `THROTTLE_ANON_RATE`, `THROTTLE_USER_RATE`, `THROTTLE_AUTH_LOGIN_RATE`, `THROTTLE_AUTH_REGISTER_RATE` |
| Email | `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` |
| Frontend | `NEXT_PUBLIC_API_URL` |
| Integrations | `ODOO_EMPLOYEES_URL`, `EXTERNAL_API_TIMEOUT_SECONDS`, `EXTERNAL_WEBHOOK_SECRET` |
| AI assistant | `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT_SECONDS` |
| CD (GitHub secrets) | `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_PATH` |

## Documentation

- [Technical specification](docs/TECHNICAL_SPEC.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Improvement plan](docs/IMPROVEMENT_PLAN.md)
- [Evaluation criteria mapping](docs/EVALUATION_CRITERIA.md)
- Final presentation material: [presentation](docs/WEEK7_PRESENTATION.md), [demo script](docs/WEEK7_DEMO_SCRIPT.md), [defense Q&A](docs/WEEK7_DEFENSE_QA.md)
- [Kazakh README](docs/README.kk.md)

## License

Built for educational and portfolio purposes. No license file is included; all rights reserved by the author.

---

Author: cristiano8518
