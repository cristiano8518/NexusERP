import logging
import time

from django.core.cache import cache
from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.employees.models import Department, Employee
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


def _scoped_employee_qs(department_id=None):
    qs = Employee.objects.filter(is_active=True)
    if department_id:
        qs = qs.filter(department_id=department_id)
    return qs


def _scoped_task_qs(department_id=None):
    qs = Task.objects.all()
    if department_id:
        qs = qs.filter(assignee__department_id=department_id)
    return qs


def get_dashboard_stats(department_id=None):
    cache_key = f"analytics:dashboard:stats:{department_id or 'all'}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    employee_qs = _scoped_employee_qs(department_id)
    task_qs = _scoped_task_qs(department_id)
    finance_qs = FinanceEntry.objects.all()
    product_qs = Product.objects.filter(is_active=True)
    if department_id:
        finance_qs = finance_qs.filter(created_by__employee_profile__department_id=department_id)
        product_qs = product_qs.filter(
            movements__created_by__employee_profile__department_id=department_id
        ).distinct()

    total_tasks = task_qs.count()
    completed_tasks = task_qs.filter(
        status__in=[Task.Status.DONE, Task.Status.APPROVED]
    ).count()
    overdue_tasks = task_qs.filter(
        deadline__lt=timezone.now(),
        status__in=[
            Task.Status.ASSIGNED,
            Task.Status.IN_PROGRESS,
            Task.Status.DONE,
            Task.Status.REJECTED,
        ],
    ).count()

    zero_money = Value(0, output_field=DecimalField(max_digits=14, decimal_places=2))
    income = finance_qs.filter(entry_type=FinanceEntry.EntryType.INCOME).aggregate(
        total=Coalesce(Sum("amount"), zero_money)
    )["total"]
    expense = finance_qs.filter(entry_type=FinanceEntry.EntryType.EXPENSE).aggregate(
        total=Coalesce(Sum("amount"), zero_money)
    )["total"]

    stats = {
        "employees": {
            "total": employee_qs.count(),
            "managers": employee_qs.filter(user__role=Role.MANAGER).count(),
            "workers": employee_qs.filter(user__role=Role.EMPLOYEE).count(),
        },
        "departments": {
            "total": Department.objects.filter(is_active=True).count()
            if not department_id
            else 1,
        },
        "tasks": {
            "total": total_tasks,
            "active": task_qs.filter(
                status__in=[
                    Task.Status.ASSIGNED,
                    Task.Status.IN_PROGRESS,
                    Task.Status.REJECTED,
                ]
            ).count(),
            "completed": completed_tasks,
            "overdue": overdue_tasks,
            "in_progress": task_qs.filter(status=Task.Status.IN_PROGRESS).count(),
            "completion_rate": round(100 * completed_tasks / total_tasks, 1) if total_tasks else 0,
        },
        "warehouse": {
            "products": product_qs.count(),
            "low_stock": product_qs.filter(quantity__lte=F("min_stock_level")).count(),
        },
        "finance": {
            "income": float(income or 0),
            "expense": float(expense or 0),
            "balance": float(income or 0) - float(expense or 0),
        },
    }

    _cache_set(cache_key, stats)
    return stats


def get_performance_stats(department_id=None):
    """Per-department, per-manager, per-employee productivity metrics."""
    cache_key = f"analytics:performance:{department_id or 'all'}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    now = timezone.now()
    departments_qs = Department.objects.filter(is_active=True)
    if department_id:
        departments_qs = departments_qs.filter(id=department_id)

    departments = []
    for dept in departments_qs.annotate(
        employee_count=Count("employees", filter=Q(employees__is_active=True)),
    ):
        dept_tasks = Task.objects.filter(assignee__department_id=dept.id)
        total = dept_tasks.count()
        completed = dept_tasks.filter(status__in=[Task.Status.DONE, Task.Status.APPROVED]).count()
        overdue = dept_tasks.filter(
            deadline__lt=now,
            status__in=[
                Task.Status.ASSIGNED,
                Task.Status.IN_PROGRESS,
                Task.Status.DONE,
                Task.Status.REJECTED,
            ],
        ).count()
        departments.append(
            {
                "id": dept.id,
                "name": dept.name,
                "employee_count": dept.employee_count,
                "manager_name": str(dept.manager) if dept.manager else None,
                "tasks_total": total,
                "tasks_completed": completed,
                "tasks_overdue": overdue,
                "completion_rate": round(100 * completed / total, 1) if total else 0,
            }
        )

    managers = []
    manager_qs = Employee.objects.filter(
        is_active=True,
        user__role=Role.MANAGER,
    ).select_related("user", "department")
    if department_id:
        manager_qs = manager_qs.filter(department_id=department_id)

    for mgr in manager_qs:
        team_tasks = Task.objects.filter(assignee__department_id=mgr.department_id)
        total = team_tasks.count()
        completed = team_tasks.filter(status__in=[Task.Status.DONE, Task.Status.APPROVED]).count()
        managers.append(
            {
                "id": mgr.id,
                "name": mgr.user.get_full_name() or mgr.user.username,
                "department": mgr.department.name,
                "team_size": Employee.objects.filter(
                    department_id=mgr.department_id,
                    is_active=True,
                    user__role=Role.EMPLOYEE,
                ).count(),
                "tasks_total": total,
                "tasks_completed": completed,
                "completion_rate": round(100 * completed / total, 1) if total else 0,
            }
        )

    employees = []
    employee_qs = Employee.objects.filter(
        is_active=True,
        user__role=Role.EMPLOYEE,
    ).select_related("user", "department")
    if department_id:
        employee_qs = employee_qs.filter(department_id=department_id)

    for emp in employee_qs:
        tasks = emp.tasks.all()
        total = tasks.count()
        completed = tasks.filter(status__in=[Task.Status.DONE, Task.Status.APPROVED]).count()
        active = tasks.filter(
            status__in=[Task.Status.ASSIGNED, Task.Status.IN_PROGRESS]
        ).count()
        overdue = tasks.filter(
            deadline__lt=now,
            status__in=[
                Task.Status.ASSIGNED,
                Task.Status.IN_PROGRESS,
                Task.Status.REJECTED,
            ],
        ).count()
        employees.append(
            {
                "id": emp.id,
                "name": emp.user.get_full_name() or emp.user.username,
                "department": emp.department.name,
                "active_tasks": active,
                "tasks_total": total,
                "tasks_completed": completed,
                "tasks_overdue": overdue,
                "completion_rate": round(100 * completed / total, 1) if total else 0,
                "workload": "busy" if active >= 3 else "normal",
            }
        )

    result = {
        "departments": departments,
        "managers": managers,
        "employees": employees,
    }
    _cache_set(cache_key, result)
    return result


def benchmark_dashboard_cache(department_id=None):
    cache.delete(f"analytics:dashboard:stats:{department_id or 'all'}")
    uncached_start = time.perf_counter()
    uncached_data = get_dashboard_stats(department_id=department_id)
    uncached_ms = round((time.perf_counter() - uncached_start) * 1000, 2)

    cached_start = time.perf_counter()
    cached_data = get_dashboard_stats(department_id=department_id)
    cached_ms = round((time.perf_counter() - cached_start) * 1000, 2)

    return {
        "cache_key": "analytics:dashboard:stats",
        "ttl_seconds": CACHE_TTL,
        "uncached_ms": uncached_ms,
        "cached_ms": cached_ms,
        "speedup_ratio": round(uncached_ms / cached_ms, 2) if cached_ms else None,
        "same_payload": uncached_data == cached_data,
    }


def get_monthly_finance(months: int = 6, department_id=None):
    from django.db.models.functions import TruncMonth

    cache_key = f"analytics:monthly:{months}:{department_id or 'all'}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    entries = (
        FinanceEntry.objects.filter(entry_date__isnull=False)
        .filter(created_by__employee_profile__department_id=department_id)
        if department_id
        else FinanceEntry.objects.filter(entry_date__isnull=False)
    )
    entries = (
        entries
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
