import csv
from decimal import Decimal

from django.db.models import F, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.employees.models import Employee
from apps.finance.models import FinanceEntry
from apps.tasks.models import Task
from apps.warehouse.models import Product, StockMovement
from common.rbac import Perm
from common.rbac.checker import PermissionChecker

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


def _department_scope(user):
    checker = PermissionChecker(user)
    if checker.has(Perm.REPORTS_VIEW_ALL):
        return None
    if checker.has(Perm.REPORTS_VIEW_DEPARTMENT):
        return checker.department_id()
    return None


def _require_reports_view(user):
    checker = PermissionChecker(user)
    if not checker.has_any(Perm.REPORTS_VIEW_ALL, Perm.REPORTS_VIEW_DEPARTMENT):
        raise PermissionDenied("Рұқсат жеткіліксіз.")


def _require_reports_export(user):
    checker = PermissionChecker(user)
    if not checker.has(Perm.REPORTS_EXPORT):
        raise PermissionDenied("Рұқсат жеткіліксіз.")


def _scoped_products(department_id=None):
    products = Product.objects.select_related("category").filter(is_active=True)
    if department_id:
        products = products.filter(
            movements__created_by__employee_profile__department_id=department_id
        ).distinct()
    return products


class ReportSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_reports_view(request.user)
        department_id = _department_scope(request.user)
        employees = Employee.objects.all()
        tasks = Task.objects.all()
        finance = FinanceEntry.objects.all()
        movements = StockMovement.objects.all()
        products = _scoped_products(department_id)
        if department_id:
            employees = employees.filter(department_id=department_id)
            tasks = tasks.filter(assignee__department_id=department_id)
            finance = finance.filter(created_by__employee_profile__department_id=department_id)
            movements = movements.filter(created_by__employee_profile__department_id=department_id)

        income = finance.filter(entry_type=FinanceEntry.EntryType.INCOME).aggregate(total=Sum("amount"))["total"]
        expense = finance.filter(entry_type=FinanceEntry.EntryType.EXPENSE).aggregate(total=Sum("amount"))["total"]
        now = timezone.now()
        task_total = tasks.count()
        task_done = tasks.filter(status__in=[Task.Status.DONE, Task.Status.APPROVED]).count()
        task_overdue = tasks.filter(deadline__lt=now).exclude(
            status__in=[Task.Status.DONE, Task.Status.APPROVED]
        ).count()
        low_stock = products.filter(quantity__lte=F("min_stock_level")).count()

        return Response(
            {
                "success": True,
                "generated_at": timezone.now(),
                "data": {
                    "employees": {
                        "active": employees.filter(is_active=True).count(),
                        "total": employees.count(),
                    },
                    "tasks": {
                        "total": task_total,
                        "done": task_done,
                        "approved": tasks.filter(status=Task.Status.APPROVED).count(),
                        "overdue": task_overdue,
                        "completion_rate": round(task_done * 100 / task_total, 1) if task_total else 0,
                    },
                    "finance": {
                        "income": _money(income),
                        "expense": _money(expense),
                        "balance": _money(income) - _money(expense),
                    },
                    "warehouse": {
                        "products": products.count(),
                        "low_stock": low_stock,
                        "movements": movements.count(),
                    },
                },
            }
        )


class AsyncReportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        _require_reports_export(request.user)
        report_type = request.data.get("report_type", "finance")
        if report_type not in {"tasks", "finance", "warehouse", "employees"}:
            return Response(
                {
                    "success": False,
                    "detail": "report_type мәні tasks, finance, warehouse немесе employees болуы керек",
                },
                status=400,
            )
        department_id = _department_scope(request.user)
        async_result = generate_report_csv_task.delay(report_type, department_id=department_id)
        return Response(
            {
                "success": True,
                "task_id": async_result.id,
                "message": "Есеп фондық режимде жасала бастады.",
            },
            status=202,
        )


class TaskReportCsvView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_reports_export(request.user)
        rows = []
        tasks = Task.objects.select_related("created_by", "assignee", "assignee__user")
        department_id = _department_scope(request.user)
        if department_id:
            tasks = tasks.filter(assignee__department_id=department_id)
        for task in tasks:
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
                    "иә" if task.is_overdue else "жоқ",
                    task.created_at,
                ]
            )
        return _csv_response(
            "nexuserp_tasks_report.csv",
            [
                "ID",
                "Атауы",
                "Статус",
                "Басымдық",
                "Құрған",
                "Орындаушы",
                "Прогресс",
                "Мерзім",
                "Мерзімі өтті",
                "Құрылған уақыты",
            ],
            rows,
        )


class FinanceReportCsvView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_reports_export(request.user)
        rows = []
        entries = FinanceEntry.objects.select_related("created_by")
        department_id = _department_scope(request.user)
        if department_id:
            entries = entries.filter(created_by__employee_profile__department_id=department_id)
        for entry in entries:
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
            ["ID", "Түрі", "Атауы", "Категория", "Сома", "Күні", "Құрған", "Сипаттама"],
            rows,
        )


class WarehouseReportCsvView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_reports_export(request.user)
        rows = []
        department_id = _department_scope(request.user)
        products = _scoped_products(department_id)
        for product in products:
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
                    "иә" if product.is_low_stock else "жоқ",
                ]
            )
        return _csv_response(
            "nexuserp_warehouse_report.csv",
            [
                "ID",
                "SKU",
                "Атауы",
                "Категория",
                "Саны",
                "Минимум қор",
                "Бағасы",
                "Қойма құны",
                "Төмен қор",
            ],
            rows,
        )


class EmployeeReportCsvView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_reports_export(request.user)
        rows = []
        employees = Employee.objects.select_related("user", "department", "position", "manager")
        department_id = _department_scope(request.user)
        checker = PermissionChecker(request.user)
        if department_id:
            employees = employees.filter(department_id=department_id)
        for employee in employees:
            rows.append(
                [
                    employee.employee_id,
                    employee.user.username,
                    employee.user.email,
                    employee.user.role,
                    employee.department.name,
                    employee.position.title,
                    employee.salary if checker.has(Perm.SYSTEM_MANAGE) else "жасырын",
                    employee.hire_date,
                    "белсенді" if employee.is_active else "белсенді емес",
                ]
            )
        return _csv_response(
            "nexuserp_employees_report.csv",
            ["Қызметкер ID", "Логин", "Email", "Рөл", "Бөлім", "Лауазым", "Жалақы", "Қабылданған күн", "Статус"],
            rows,
        )
