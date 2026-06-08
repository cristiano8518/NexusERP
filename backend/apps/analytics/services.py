import logging
import time

from django.core.cache import cache
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce

from apps.employees.models import Employee
from apps.finance.models import FinanceEntry
from apps.tasks.models import Task
from apps.warehouse.models import Product

logger = logging.getLogger("nexuserp")

CACHE_TTL = 300


def _cache_get(key):
    try:
        return cache.get(key)
    except Exception as exc:
        logger.warning("Cache get failed: %s", exc)
        return None


def _cache_set(key, value, ttl=CACHE_TTL):
    try:
        cache.set(key, value, ttl)
    except Exception as exc:
        logger.warning("Cache set failed: %s", exc)


def get_dashboard_stats():
    cache_key = "analytics:dashboard:stats"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(
        status__in=[Task.Status.DONE, Task.Status.APPROVED]
    ).count()

    zero_money = Value(0, output_field=DecimalField(max_digits=14, decimal_places=2))
    income = FinanceEntry.objects.filter(entry_type=FinanceEntry.EntryType.INCOME).aggregate(
        total=Coalesce(Sum("amount"), zero_money)
    )["total"]
    expense = FinanceEntry.objects.filter(entry_type=FinanceEntry.EntryType.EXPENSE).aggregate(
        total=Coalesce(Sum("amount"), zero_money)
    )["total"]

    stats = {
        "employees": {
            "total": Employee.objects.filter(is_active=True).count(),
        },
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
            "in_progress": Task.objects.filter(status=Task.Status.IN_PROGRESS).count(),
            "completion_rate": round(100 * completed_tasks / total_tasks, 1) if total_tasks else 0,
        },
        "warehouse": {
            "products": Product.objects.filter(is_active=True).count(),
            "low_stock": Product.objects.filter(is_active=True)
            .filter(quantity__lte=F("min_stock_level"))
            .count(),
        },
        "finance": {
            "income": float(income or 0),
            "expense": float(expense or 0),
            "balance": float(income or 0) - float(expense or 0),
        },
    }

    _cache_set(cache_key, stats)
    return stats


def benchmark_dashboard_cache():
    cache.delete("analytics:dashboard:stats")
    uncached_start = time.perf_counter()
    uncached_data = get_dashboard_stats()
    uncached_ms = round((time.perf_counter() - uncached_start) * 1000, 2)

    cached_start = time.perf_counter()
    cached_data = get_dashboard_stats()
    cached_ms = round((time.perf_counter() - cached_start) * 1000, 2)

    return {
        "cache_key": "analytics:dashboard:stats",
        "ttl_seconds": CACHE_TTL,
        "uncached_ms": uncached_ms,
        "cached_ms": cached_ms,
        "speedup_ratio": round(uncached_ms / cached_ms, 2) if cached_ms else None,
        "same_payload": uncached_data == cached_data,
    }


def get_monthly_finance(months: int = 6):
    from django.db.models.functions import TruncMonth

    cache_key = f"analytics:monthly:{months}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    entries = (
        FinanceEntry.objects.filter(entry_date__isnull=False)
        .annotate(month=TruncMonth("entry_date"))
        .values("month", "entry_type")
        .annotate(
            total=Coalesce(
                Sum("amount"),
                Value(0, output_field=DecimalField(max_digits=14, decimal_places=2)),
            )
        )
        .order_by("month")
    )

    monthly: dict[str, dict] = {}
    for row in entries:
        key = row["month"].strftime("%Y-%m") if row["month"] else "unknown"
        if key not in monthly:
            monthly[key] = {"month": key, "income": 0.0, "expense": 0.0}
        amount = float(row["total"] or 0)
        if row["entry_type"] == FinanceEntry.EntryType.INCOME:
            monthly[key]["income"] = amount
        else:
            monthly[key]["expense"] = amount

    result = sorted(monthly.values(), key=lambda x: x["month"])[-months:]
    _cache_set(cache_key, result)
    return result
