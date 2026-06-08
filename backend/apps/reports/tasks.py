import csv
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.utils import timezone


@shared_task(name="reports.generate_csv")
def generate_report_csv_task(report_type: str) -> dict:
    from apps.employees.models import Employee
    from apps.finance.models import FinanceEntry
    from apps.tasks.models import Task
    from apps.warehouse.models import Product

    report_dir = Path(settings.MEDIA_ROOT) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{report_type}-{timestamp}.csv"
    file_path = report_dir / filename

    report_map = {
        "tasks": (
            ["ID", "Title", "Status", "Priority", "Progress", "Deadline"],
            [
                [task.id, task.title, task.status, task.priority, task.progress, task.deadline or ""]
                for task in Task.objects.all()
            ],
        ),
        "finance": (
            ["ID", "Type", "Title", "Category", "Amount", "Date"],
            [
                [entry.id, entry.entry_type, entry.title, entry.category, entry.amount, entry.entry_date]
                for entry in FinanceEntry.objects.all()
            ],
        ),
        "warehouse": (
            ["SKU", "Name", "Quantity", "Min stock", "Price"],
            [
                [product.sku, product.name, product.quantity, product.min_stock_level, product.price]
                for product in Product.objects.all()
            ],
        ),
        "employees": (
            ["Employee ID", "Username", "Role", "Department", "Position"],
            [
                [
                    employee.employee_id,
                    employee.user.username,
                    employee.user.role,
                    employee.department.name,
                    employee.position.title,
                ]
                for employee in Employee.objects.select_related("user", "department", "position")
            ],
        ),
    }

    if report_type not in report_map:
        raise ValueError(f"Unsupported report type: {report_type}")

    headers, rows = report_map[report_type]
    with file_path.open("w", newline="", encoding="utf-8-sig") as report_file:
        writer = csv.writer(report_file)
        writer.writerow(headers)
        writer.writerows(rows)

    return {
        "report_type": report_type,
        "filename": filename,
        "path": str(file_path),
        "url": f"{settings.MEDIA_URL}reports/{filename}",
        "rows": len(rows),
    }
