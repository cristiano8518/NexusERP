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

> Барлық `docker compose ...` командаларын міндетті түрде `C:\Users\user\NexusERP`
> папкасынан орындаңыз. Әйтпесе Docker `no configuration file provided` қатесін береді.

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

### 4. Масштабты demo data

Dashboard, Tasks, Finance, Warehouse, Analytics & Reports бөлімдері бос көрінбеуі үшін
realistic үлкен dataset құюға болады:

```powershell
.\scripts\seed-scale-demo.ps1
```

Немесе қолмен:

```powershell
docker compose exec backend python manage.py seed_scale_demo --reset-scale --employees 48 --tasks 240 --finance 220 --movements 160
```

Бұл команда мыналарды қосады:

- 6 бөлім және бірнеше лауазым;
- 48 қызметкер және бірнеше manager;
- 240 workflow тапсырма;
- 220 қаржы жазбасы;
- 12 өнім және 160 қойма қозғалысы;
- task activity, comments және notifications.

Demo login:

```text
admin / admin123
manager / manager123
scale_manager_01 / manager123
scale_employee_001 / employee123
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
- `docs/EVALUATION_CRITERIA.md` — 1–7 апта критерийлерінің орындалуын дәлелдеу.
- `docs/IMPROVEMENT_PLAN.md` — жетіспейтін жерлер, түзетілген қателер және next roadmap.
- `docs/WEEK7_PRESENTATION.md` — финал презентация құрылымы.
- `docs/WEEK7_DEMO_SCRIPT.md` — live demo жүргізу сценариі.
- `docs/WEEK7_DEFENSE_QA.md` — қорғауға дайын Q&A.

### Week 5–7 жаңартуы

- **Week 5 (Automated Testing):** `tasks`, `finance`, `warehouse`, `integrations` модульдеріне API тесттері қосылды.
- **Coverage gate:** CI ішінде `pytest-cov` арқылы coverage есептеледі, `--cov-fail-under=40` енгізілді.
- **Week 6 (Security/CD):** DRF rate limiting (`THROTTLE_ANON_RATE`, `THROTTLE_USER_RATE`, `THROTTLE_AUTH_LOGIN_RATE`, `THROTTLE_AUTH_REGISTER_RATE`) қосылды.
- **CD pipeline:** `.github/workflows/cd.yml` арқылы `main` branch push және manual dispatch кезінде deploy сценарийі іске қосылады (SSH secrets қажет).

Негізгі verification endpoint-тер:

```text
GET  /api/v1/analytics/cache-benchmark/
POST /api/v1/reports/async/
POST /api/v1/notifications/bulk-email/
POST /api/v1/ai/chat/
GET  /api/v1/integrations/external-employees/
POST /api/v1/integrations/external-employees/
POST /api/v1/integrations/webhooks/external/
```

Webhook қолтаңбасы (security):

```text
X-Nexus-Timestamp: <unix_timestamp>
X-Nexus-Signature: sha256=<hmac_sha256(timestamp + "." + raw_body, secret)>
```

## Ollama AI көмекші

NexusERP ішінде локалды AI көмекші бар: `Басты бет → AI көмекші`.
Frontend тікелей Ollama-ға қосылмайды; сұрақ алдымен Django endpoint-ке барады, backend рөлге сай ERP context жинап, Ollama-ға жібереді.

Компьютерде Ollama іске қосыңыз:

```powershell
ollama serve
ollama pull llama3.1:8b
```

`.env` ішінде:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_TIMEOUT_SECONDS=60
```

Егер backend Docker ішінде емес, тікелей Windows-та іске қосылса, `OLLAMA_BASE_URL=http://localhost:11434` деп ауыстыруға болады.

## Рөлдер

| Рөл | Код |
|-----|-----|
| Админ | `admin` |
| Менеджер | `manager` |
| Қызметкер | `employee` |

Логика:

- **Админ** барлық бөлімдерді, қызметкерлерді, тапсырмаларды, қаржы жазбаларын және есептерді көреді.
- **Менеджер** тек өзінің HR профиліндегі бөлімге байланысты деректерді қадағалайды: сол бөлімнің қызметкерлері, тапсырмалары, бөлім бойынша analytics/report көрсеткіштері.
- **Қызметкер** тек өзіне берілген тапсырмаларды көреді және прогресті жаңарта алады.

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

## Жоба статусы

NexusERP қазіргі күйі:

- ✅ **Week 1–4** толық орындалған (архитектура, DB/кэш, background jobs, integrations)
- ✅ **Week 5** орындалған (backend API тесттер + CI coverage gate)
- ✅ **Week 6** орындалған (production-like deploy, rate limit, CD workflow)
- ✅ **Week 7** орындалған (presentation, demo script, defense Q&A)

Қазіргі функционал:

- Толық ERP модульдері: қызметкерлер, тапсырмалар, қойма, қаржы, аналитика/есеп, хабарламалар, интеграциялар, AI көмекші.
- Рөлдік модель толық іске асқан: admin/manager/employee, manager — department scope.
- Production-ready инфрақұрылым: `docker-compose.prod.yml`, Nginx reverse proxy, backup script, CI/CD workflow.

Келесі даму идеялары (міндетті емес, post-course roadmap):

- Telegram интеграциясы
- Мониторинг және алертинг (metrics + logs)
- Қосымша e2e тесттер

## Лицензия

Жоба оқу/портфолио мақсатында.
