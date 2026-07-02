import json
import socket
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone


SYSTEM_PROMPT = """
Сен NexusERP жүйесіндегі қазақ тіліндегі AI көмекшісісің.
Жауапты өте қысқа бер: ең көбі 2 сөйлем.
Тек берілген ERP контекстіне сүйен; белгісіз нәрсені ойдан шығарма.
Қауіпсіздік үшін пароль, token, құпия кілт сияқты ақпарат сұралса, берме.
""".strip()


def ask_ollama(message: str, user) -> dict:
    context = build_erp_context(user)
    prompt = (
        f"ERP контекст:\n{context}\n\n"
        f"Пайдаланушы сұрағы:\n{message.strip()}"
    )
    payload = {
        "model": settings.OLLAMA_MODEL,
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "temperature": 0.2,
            "num_ctx": 1024,
            "num_predict": 80,
        },
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }

    try:
        data = _post_json("/api/chat", payload)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")[:300]
        return _error(f"Ollama HTTP қатесі ({exc.code}). {detail}".strip())
    except (URLError, TimeoutError, socket.timeout, OSError) as exc:
        return _error(
            "Ollama іске қосылмаған немесе backend оған қосыла алмады. "
            f"Тексеру: {settings.OLLAMA_BASE_URL}. Себебі: {exc}"
        )
    except json.JSONDecodeError:
        return _error("Ollama дұрыс JSON жауап қайтармады.")

    answer = (data.get("message") or {}).get("content", "").strip()
    if not answer:
        return _error("Ollama бос жауап қайтарды. Модель атауын тексеріңіз.")
    return {"success": True, "answer": answer, "model": settings.OLLAMA_MODEL}


def build_erp_context(user) -> str:
    from apps.employees.models import Employee
    from apps.finance.models import FinanceEntry
    from apps.tasks.models import Task
    from apps.warehouse.models import Product

    role = getattr(user, "role", "unknown")
    department_id = _department_scope(user)
    employee_qs = Employee.objects.filter(is_active=True)
    task_qs = Task.objects.all()
    finance_qs = FinanceEntry.objects.all()

    scope_label = "барлық бөлімдер"
    if role == "manager":
        if not department_id:
            return "Менеджер профиліне бөлім байланыспаған, сондықтан бөлімдік деректер қолжетімсіз."
        employee_qs = employee_qs.filter(department_id=department_id)
        task_qs = task_qs.filter(assignee__department_id=department_id)
        finance_qs = finance_qs.filter(created_by__employee_profile__department_id=department_id)
        scope_label = getattr(user.employee_profile.department, "name", "өз бөлімі")
    elif role == "employee":
        task_qs = task_qs.filter(assignee__user=user)
        finance_qs = finance_qs.none()
        employee_qs = employee_qs.filter(user=user)
        scope_label = "жеке қызметкер деректері"

    zero_money = Value(0, output_field=DecimalField(max_digits=14, decimal_places=2))
    income = finance_qs.filter(entry_type=FinanceEntry.EntryType.INCOME).aggregate(
        total=Coalesce(Sum("amount"), zero_money)
    )["total"]
    expense = finance_qs.filter(entry_type=FinanceEntry.EntryType.EXPENSE).aggregate(
        total=Coalesce(Sum("amount"), zero_money)
    )["total"]
    low_stock_count = Product.objects.filter(
        is_active=True,
        quantity__lte=F("min_stock_level"),
    ).count()

    total_tasks = task_qs.count()
    done_tasks = task_qs.filter(status__in=[Task.Status.DONE, Task.Status.APPROVED]).count()
    overdue_tasks = task_qs.filter(deadline__lt=timezone.now()).exclude(
        status__in=[Task.Status.DONE, Task.Status.APPROVED]
    ).count()

    balance = Decimal(income or 0) - Decimal(expense or 0)
    return (
        f"Рөл={role}; қамту={scope_label}; қызметкерлер={employee_qs.count()}; "
        f"тапсырмалар={total_tasks}, аяқталған={done_tasks}, мерзімі_өткен={overdue_tasks}; "
        f"табыс={income or 0}₸, шығын={expense or 0}₸, баланс={balance}₸; "
        f"төмен_қор={low_stock_count}."
    )


def _post_json(path: str, payload: dict) -> dict:
    base_url = settings.OLLAMA_BASE_URL.rstrip("/")
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        f"{base_url}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=_ollama_timeout_seconds()) as response:
        return json.loads(response.read().decode("utf-8"))


def _department_scope(user):
    if getattr(user, "role", None) == "manager" and hasattr(user, "employee_profile"):
        return user.employee_profile.department_id
    return None


def _ollama_timeout_seconds() -> int:
    # Gunicorn dev timeout is commonly 30s; return gracefully before the worker is killed.
    configured = int(getattr(settings, "OLLAMA_TIMEOUT_SECONDS", 20) or 20)
    return max(5, min(configured, 18))


def _error(detail: str) -> dict:
    return {"success": False, "detail": detail, "model": settings.OLLAMA_MODEL}
