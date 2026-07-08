import csv
import logging
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("nexuserp")


def _filter_by_department(queryset, department_id, path):
    if not department_id:
        return queryset
    return queryset.filter(**{path: department_id})


@shared_task(
    name="reports.generate_csv",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def generate_report_csv_task(self, report_type: str, department_id=None) -> dict:
    from apps.employees.models import Employee
    from apps.finance.models import FinanceEntry
    from apps.tasks.models import Task
    from apps.warehouse.models import Product

    report_dir = Path(settings.MEDIA_ROOT) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    scope = f"dept{department_id}" if department_id else "all"
    filename = f"{report_type}-{scope}-{timestamp}.csv"
    file_path = report_dir / filename

    tasks_qs = Task.objects.all()
    finance_qs = FinanceEntry.objects.all()
    products_qs = Product.objects.filter(is_active=True)
    employees_qs = Employee.objects.select_related("user", "department", "position")

    if department_id:
        tasks_qs = tasks_qs.filter(assignee__department_id=department_id)
        finance_qs = finance_qs.filter(created_by__employee_profile__department_id=department_id)
        products_qs = products_qs.filter(
            movements__created_by__employee_profile__department_id=department_id
        ).distinct()
        employees_qs = employees_qs.filter(department_id=department_id)

    report_map = {
        "tasks": (
            ["ID", "Атауы", "Статус", "Басымдық", "Прогресс", "Мерзім"],
            [
                [task.id, task.title, task.status, task.priority, task.progress, task.deadline or ""]
                for task in tasks_qs
            ],
        ),
        "finance": (
            ["ID", "Түрі", "Атауы", "Категория", "Сома", "Күні"],
            [
                [entry.id, entry.entry_type, entry.title, entry.category, entry.amount, entry.entry_date]
                for entry in finance_qs
            ],
        ),
        "warehouse": (
            ["SKU", "Атауы", "Саны", "Минимум қор", "Бағасы"],
            [
                [product.sku, product.name, product.quantity, product.min_stock_level, product.price]
                for product in products_qs
            ],
        ),
        "employees": (
            ["Қызметкер ID", "Логин", "Рөл", "Бөлім", "Лауазым"],
            [
                [
                    employee.employee_id,
                    employee.user.username,
                    employee.user.role,
                    employee.department.name,
                    employee.position.title,
                ]
                for employee in employees_qs
            ],
        ),
    }

    if report_type not in report_map:
        raise ValueError(f"Қолдау көрсетілмейтін есеп түрі: {report_type}")

    headers, rows = report_map[report_type]
    with file_path.open("w", newline="", encoding="utf-8-sig") as report_file:
        writer = csv.writer(report_file)
        writer.writerow(headers)
        writer.writerows(rows)

    logger.info("Generated async report %s rows=%s scope=%s", filename, len(rows), scope)
    return {
        "report_type": report_type,
        "department_id": department_id,
        "filename": filename,
        "path": str(file_path),
        "url": f"{settings.MEDIA_URL}reports/{filename}",
        "rows": len(rows),
    }
