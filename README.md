# NexusERP

Корпоративтік ERP жүйесі — қызметкерлер, тапсырмалар, қойма, қаржы және аналитиканы бір орталықтан басқару.

## Технологиялар

| Қабат | Стек |
|-------|------|
| Backend | Django 5, Django REST Framework, JWT, Celery |
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| DB | PostgreSQL 16 |
| Cache / Queue | Redis 7 |
| Infra | Docker Compose, GitHub Actions |

## Жоба құрылымы

```
NexusERP/
├── backend/          # Django API
│   ├── config/       # Settings, URLs, Celery
│   ├── apps/         # Модульдер (accounts, employees, …)
│   └── common/       # Ортақ утилиталар
├── frontend/         # Next.js UI
├── docs/             # Technical spec, evaluation mapping
├── nginx/            # Production reverse proxy
├── docker-compose.yml
├── docker-compose.prod.yml
└── .github/workflows/
```

## Жылдам бастау

### 1. Environment

```bash
cd NexusERP
copy .env.example .env
```

`.env` ішінде `SECRET_KEY` өзгертіңіз.

### 2. Docker (ұсынылады)

```bash
docker compose up --build
```

| Сервис | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000/api/v1/ |
| Swagger | http://localhost:8000/api/docs/ |
| Admin (Jazzmin UI) | http://localhost:8000/admin/ |

### 2.1 Healthcheck

```powershell
.\scripts\healthcheck.ps1
```

### 3. Суперпайдаланушы (бірінші рет)

```bash
docker compose exec backend python manage.py createsuperuser
```

## Модульдер (фундамент)

- **accounts** — Auth, JWT, рөлдер, қауіпсіздік логтары
- **employees** — HR Pro: бөлімдер, лауазымдар, employee profile, task summary, salary visibility
- **tasks** — Тапсырмалар, workflow, status timeline, comments, activity history
- **warehouse** — Тауар, қалдық, кіріс/шығыс, product history, finance integration
- **finance** — Кіріс/шығын, category breakdown, cashflow, warehouse auto entries
- **analytics** — Dashboard агрегациялары, reports export center, printable PDF view
- **notifications** — Notification Center, unread count, Celery email/хабарламалар
- **reports** — Backend CSV export API for Analytics & Reports
- **integrations** — External API sync, webhook қабылдау, timeout/error handling

## Бағалау критерийлері

Курстық/апталық критерийлер mapping:

- `docs/TECHNICAL_SPEC.md` — техникалық тапсырма және архитектура.
- `docs/EVALUATION_CRITERIA.md` — 1–4 апта критерийлерінің орындалуын дәлелдеу.

Негізгі verification endpoint-тер:

```text
GET  /api/v1/analytics/cache-benchmark/
POST /api/v1/reports/async/
POST /api/v1/notifications/bulk-email/
GET  /api/v1/integrations/external-employees/
POST /api/v1/integrations/external-employees/
POST /api/v1/integrations/webhooks/external/
```

## Рөлдер

| Рөл | Код |
|-----|-----|
| Админ | `admin` |
| Менеджер | `manager` |
| Қызметкер | `employee` |

## Production-like Deploy

Production stack Nginx арқылы бір портта жұмыс істейді:

| Route | Service |
|-------|---------|
| `/` | Next.js frontend |
| `/api/` | Django API |
| `/admin/` | Django Admin |
| `/static/`, `/media/` | Nginx static/media |

### 1. Production env

```powershell
copy .env.production.example .env.production
```

`.env.production` ішінде міндетті түрде өзгертіңіз:

- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- email SMTP values

### 2. Start production-like stack

```powershell
.\scripts\prod-deploy.ps1
```

Немесе қолмен:

```powershell
docker compose -f docker-compose.prod.yml --env-file .env.production up --build -d
```

URL:

```text
http://localhost
```

### 3. Database backup

Development stack үшін:

```powershell
.\scripts\backup-db.ps1
```

Production stack үшін:

```powershell
.\scripts\backup-prod-db.ps1
```

### 4. Logs

```powershell
docker compose -f docker-compose.prod.yml --env-file .env.production logs backend --tail 100
docker compose -f docker-compose.prod.yml --env-file .env.production logs nginx --tail 100
```

## Дамыту фазалары

1. ✅ Фаза 0 — Фундамент (Docker, apps, JWT, UI shell)
2. ✅ Фаза 1 — Auth (register, AuthGuard, рөл бойынша меню)
3. ✅ Фаза 2–5 (негізгі UI) — Employees, Tasks workflow, Warehouse, Finance
4. ✅ Фаза 6 — Recharts, monthly finance, security logs (admin)
5. ✅ HR create (admin), Warehouse in/out, Email on new task (Celery)
6. ✅ Task Workflow Pro — detail page, comments, activity history, approve/reject logic
7. ✅ Kanban Board — Assigned / In Progress / Review / Approved / Rejected
8. ✅ Notification Center — bell dropdown, unread count, task workflow events
9. ✅ Warehouse + Finance — stock movement validation, auto income/expense, product detail history
10. ✅ Analytics & Reports — KPI, monthly finance, CSV exports + Print/PDF
11. ✅ HR Module Pro — employee detail, structure management, salary visibility
12. ✅ UI Polish — toast notifications, reusable loading/empty states, confirm dialog foundation
13. ✅ Production readiness — prod compose, Nginx, env template, healthcheck, backup
14. ✅ Finance Pro — category breakdown, filters, edit/delete, monthly cashflow
15. ⏳ Келесі — Telegram, advanced monitoring

## Лицензия

Жоба оқу/портфолио мақсатында.
