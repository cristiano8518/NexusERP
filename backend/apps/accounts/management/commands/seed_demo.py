from django.core.management.base import BaseCommand

from apps.accounts.models import Role, User
from apps.employees.models import Department, Employee, Position
from apps.finance.models import FinanceEntry
from apps.notifications.models import Notification
from apps.tasks.models import Task, TaskActivity, TaskComment
from apps.warehouse.models import Category, Product, StockMovement
from datetime import date


class Command(BaseCommand):
    help = "Create demo admin, manager, employee and sample data"

    def handle(self, *args, **options):
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@nexuserp.local",
                "role": Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "first_name": "Админ",
            },
        )
        admin.set_password("admin123")
        admin.is_active = True
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        manager, _ = User.objects.get_or_create(
            username="manager",
            defaults={
                "email": "manager@nexuserp.local",
                "role": Role.MANAGER,
                "first_name": "Менеджер",
            },
        )
        manager.set_password("manager123")
        manager.is_active = True
        manager.save()

        employee_user, _ = User.objects.get_or_create(
            username="employee",
            defaults={
                "email": "employee@nexuserp.local",
                "role": Role.EMPLOYEE,
                "first_name": "Қызметкер",
            },
        )
        employee_user.set_password("employee123")
        employee_user.is_active = True
        employee_user.save()

        dept, _ = Department.objects.get_or_create(
            name="HR",
            defaults={"description": "Адам ресурстары"},
        )
        pos, _ = Position.objects.get_or_create(
            title="Менеджер",
            department=dept,
            defaults={"base_salary": 500000},
        )

        if not hasattr(employee_user, "employee_profile"):
            Employee.objects.create(
                user=employee_user,
                department=dept,
                position=pos,
                employee_id="EMP-001",
                hire_date=date.today(),
                salary=350000,
            )

        cat, _ = Category.objects.get_or_create(name="Жабдықтар")
        product, _ = Product.objects.get_or_create(
            sku="SKU-001",
            defaults={
                "name": "Ноутбук",
                "category": cat,
                "quantity": 5,
                "min_stock_level": 2,
                "price": 450000,
            },
        )
        StockMovement.objects.get_or_create(
            product=product,
            movement_type=StockMovement.MovementType.IN,
            note="Demo бастапқы қойма кірісі",
            defaults={
                "quantity": 5,
                "unit_price": product.price,
                "auto_create_finance": False,
                "created_by": manager,
            },
        )

        emp_profile = getattr(employee_user, "employee_profile", None)
        task, _ = Task.objects.get_or_create(
            title="Айлық есеп дайындау",
            defaults={
                "description": "Қаржы бөліміне есеп жіберу",
                "created_by": manager,
                "assignee": emp_profile,
                "status": Task.Status.ASSIGNED,
                "priority": Task.Priority.HIGH,
            },
        )
        TaskActivity.objects.get_or_create(
            task=task,
            action=TaskActivity.Action.CREATED,
            defaults={
                "actor": manager,
                "to_status": task.status,
                "message": "Demo тапсырма workflow showcase үшін жасалды.",
            },
        )
        TaskComment.objects.get_or_create(
            task=task,
            author=manager,
            message="Есепті дайындап, тексеруге жіберіңіз.",
        )
        Notification.objects.get_or_create(
            recipient=employee_user,
            notification_type=Notification.Type.TASK_ASSIGNED,
            title=f"Жаңа тапсырма: {task.title}",
            defaults={
                "actor": manager,
                "priority": Notification.Priority.HIGH,
                "message": "Demo workflow үшін тапсырма берілді.",
                "link": f"/dashboard/tasks/{task.id}",
                "metadata": {"task_id": task.id},
            },
        )

        FinanceEntry.objects.get_or_create(
            title="Қызмет көрсету",
            entry_date=date.today(),
            defaults={
                "entry_type": FinanceEntry.EntryType.INCOME,
                "amount": 1200000,
                "category": "Sales",
                "created_by": manager,
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("  admin / admin123")
        self.stdout.write("  manager / manager123")
        self.stdout.write("  employee / employee123")
