import csv
from decimal import Decimal

from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.employees.models import Employee
from apps.finance.models import FinanceEntry
from apps.tasks.models import Task
from apps.warehouse.models import Product, StockMovement
from common.permissions import IsManagerOrAdmin
from .tasks import generate_report_csv_task


def _money(value):
    return float(value or Decimal("0"))


def _csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
    return response


class ReportSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        income = FinanceEntry.objects.filter(entry_type=FinanceEntry.EntryType.INCOME).aggregate(
            total=Sum("amount")
        )["total"]
        expense = FinanceEntry.objects.filter(entry_type=FinanceEntry.EntryType.EXPENSE).aggregate(
            total=Sum("amount")
        )["total"]
        task_total = Task.objects.count()
        task_done = Task.objects.filter(status__in=[Task.Status.DONE, Task.Status.APPROVED]).count()

        return Response(
            {
                "success": True,
                "generated_at": timezone.now(),
                "data": {
                    "employees": {
                        "active": Employee.objects.filter(is_active=True).count(),
                        "total": Employee.objects.count(),
                    },
                    "tasks": {
                        "total": task_total,
                        "done": task_done,
                        "approved": Task.objects.filter(status=Task.Status.APPROVED).count(),
                        "overdue": sum(1 for task in Task.objects.all() if task.is_overdue),
                        "completion_rate": round(task_done * 100 / task_total, 1) if task_total else 0,
                    },
                    "finance": {
                        "income": _money(income),
                        "expense": _money(expense),
                        "balance": _money(income) - _money(expense),
                    },
                    "warehouse": {
                        "products": Product.objects.filter(is_active=True).count(),
                        "low_stock": sum(1 for product in Product.objects.filter(is_active=True) if product.is_low_stock),
                        "movements": StockMovement.objects.count(),
                    },
                },
            }
        )


class AsyncReportView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def post(self, request):
        report_type = request.data.get("report_type", "finance")
        if report_type not in {"tasks", "finance", "warehouse", "employees"}:
            return Response(
                {
                    "success": False,
                    "detail": "report_type must be one of: tasks, finance, warehouse, employees",
                },
                status=400,
            )
        async_result = generate_report_csv_task.delay(report_type)
        return Response(
            {
                "success": True,
                "task_id": async_result.id,
                "message": "Report generation started in background.",
            },
            status=202,
        )


class TaskReportCsvView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        rows = []
        for task in Task.objects.select_related("created_by", "assignee", "assignee__user"):
            rows.append(
                [
                    task.id,
                    task.title,
                    task.get_status_display(),
                    task.get_priority_display(),
                    task.created_by.username,
                    task.assignee.user.username if task.assignee else "",
                    task.progress,
                    task.deadline or "",
                    "yes" if task.is_overdue else "no",
                    task.created_at,
                ]
            )
        return _csv_response(
            "nexuserp_tasks_report.csv",
            [
                "ID",
                "Title",
                "Status",
                "Priority",
                "Created by",
                "Assignee",
                "Progress",
                "Deadline",
                "Overdue",
                "Created at",
            ],
            rows,
        )


class FinanceReportCsvView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        rows = []
        for entry in FinanceEntry.objects.select_related("created_by"):
            rows.append(
                [
                    entry.id,
                    entry.get_entry_type_display(),
                    entry.title,
                    entry.category,
                    entry.amount,
                    entry.entry_date,
                    entry.created_by.username if entry.created_by else "",
                    entry.description,
                ]
            )
        return _csv_response(
            "nexuserp_finance_report.csv",
            ["ID", "Type", "Title", "Category", "Amount", "Date", "Created by", "Description"],
            rows,
        )


class WarehouseReportCsvView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        rows = []
        for product in Product.objects.select_related("category"):
            rows.append(
                [
                    product.id,
                    product.sku,
                    product.name,
                    product.category.name,
                    product.quantity,
                    product.min_stock_level,
                    product.price,
                    product.quantity * product.price,
                    "yes" if product.is_low_stock else "no",
                ]
            )
        return _csv_response(
            "nexuserp_warehouse_report.csv",
            [
                "ID",
                "SKU",
                "Name",
                "Category",
                "Quantity",
                "Min stock",
                "Price",
                "Inventory value",
                "Low stock",
            ],
            rows,
        )


class EmployeeReportCsvView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        rows = []
        for employee in Employee.objects.select_related("user", "department", "position", "manager"):
            rows.append(
                [
                    employee.employee_id,
                    employee.user.username,
                    employee.user.email,
                    employee.user.role,
                    employee.department.name,
                    employee.position.title,
                    employee.salary if request.user.role == "admin" else "hidden",
                    employee.hire_date,
                    "active" if employee.is_active else "inactive",
                ]
            )
        return _csv_response(
            "nexuserp_employees_report.csv",
            ["Employee ID", "Username", "Email", "Role", "Department", "Position", "Salary", "Hire date", "Status"],
            rows,
        )
