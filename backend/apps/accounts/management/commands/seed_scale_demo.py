import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.employees.models import Department, Employee, Position
from apps.finance.models import FinanceEntry
from apps.notifications.models import Notification
from apps.tasks.models import Task, TaskActivity, TaskComment
from apps.warehouse.models import Category, Product, StockMovement

DEPARTMENTS = {
    "Операциялар": ["Операциялар менеджері", "Процесс аналитигі", "Кеңсе үйлестірушісі"],
    "Сату": ["Сату менеджері", "Клиент менеджері", "Клиент қолдау маманы"],
    "Қаржы": ["Қаржы менеджері", "Бухгалтер", "Қаржы аналитигі"],
    "HR": ["HR менеджері", "Рекрутер", "HR маманы"],
    "IT": ["IT менеджері", "Backend әзірлеуші", "Қолдау инженері"],
    "Қойма": ["Қойма менеджері", "Қор есебі маманы", "Логистика үйлестірушісі"],
}

PRODUCT_CATALOG = [
    ("LTP-001", "Lenovo ThinkPad E14", "IT жабдықтары", 420000, 4),
    ("LTP-002", "MacBook Air M2", "IT жабдықтары", 680000, 3),
    ("MON-024", "Dell 24 монитор", "IT жабдықтары", 95000, 8),
    ("KEY-101", "Logitech пернетақта", "Кеңсе жабдықтары", 22000, 12),
    ("MOU-202", "Сымсыз тінтуір", "Кеңсе жабдықтары", 14000, 15),
    ("CHR-010", "Эргономикалық орындық", "Кеңсе жиһазы", 78000, 6),
    ("DSK-020", "Кеңсе үстелі", "Кеңсе жиһазы", 115000, 5),
    ("PPR-500", "A4 қағаз қорабы", "Шығын материалдары", 12500, 20),
    ("INK-774", "Принтер бояуы", "Шығын материалдары", 31000, 10),
    ("PRN-300", "HP Laser принтері", "Кеңсе жабдықтары", 185000, 3),
    ("RTR-900", "MikroTik роутері", "Желі жабдықтары", 65000, 4),
    ("SWC-024", "24 порттық switch", "Желі жабдықтары", 155000, 2),
]

TASK_TEMPLATES = [
    "Айлық қаржы есебін дайындау",
    "Қойма қалдығын салыстыру",
    "Клиент келісімшартын тексеру",
    "Жаңа қызметкерді бейімдеу тізімі",
    "Сату воронкасын талдау",
    "Инвентаризация актісін дайындау",
    "API интеграция статусын тексеру",
    "HR нәтижелерінің қорытындысы",
    "Жабдық сатып алу сұранысын өңдеу",
    "Төлем құжаттарын тексеру",
    "Басқару панелі KPI сапасын тексеру",
    "Қауіпсіздік логтарын талдау",
]

FINANCE_CATEGORIES = [
    "Сату",
    "Қызмет көрсету",
    "Қойма",
    "Жалақы",
    "Кеңсе",
    "Көлік",
    "Маркетинг",
    "Бағдарламалық қамту",
]


class Command(BaseCommand):
    help = "Басқару панелі, аналитика және есептер үшін үлкен demo dataset жасау."

    def add_arguments(self, parser):
        parser.add_argument("--employees", type=int, default=36)
        parser.add_argument("--tasks", type=int, default=180)
        parser.add_argument("--finance", type=int, default=160)
        parser.add_argument("--movements", type=int, default=120)
        parser.add_argument(
            "--reset-scale",
            action="store_true",
            help="Remove previously generated SCALE demo data before seeding.",
        )

    def handle(self, *args, **options):
        random.seed(42)
        if options["reset_scale"]:
            self._reset_scale_data()

        admin = self._ensure_user("admin", "admin123", Role.ADMIN, "Админ", "Nexus")
        manager = self._ensure_user("manager", "manager123", Role.MANAGER, "Мирас", "Менеджер")

        departments, positions = self._seed_structure()
        self._ensure_base_manager_profile(manager, departments, positions)
        managers = self._seed_managers(departments, positions, manager)
        employees = self._seed_employees(options["employees"], departments, positions, managers)
        products = self._seed_products()
        self._seed_movements(options["movements"], products, manager)
        self._seed_finance(options["finance"], admin, manager)
        self._seed_tasks(options["tasks"], employees, managers)
        self._seed_notifications(employees, managers)

        cache.clear()
        self.stdout.write(self.style.SUCCESS("Scale demo data ready."))
        self.stdout.write(f"  қызметкерлер: {Employee.objects.count()}")
        self.stdout.write(f"  тапсырмалар: {Task.objects.count()}")
        self.stdout.write(f"  қаржы жазбалары: {FinanceEntry.objects.count()}")
        self.stdout.write(f"  тауарлар: {Product.objects.count()}")
        self.stdout.write(f"  stock movements: {StockMovement.objects.count()}")
        self.stdout.write("")
        self.stdout.write("Demo logins:")
        self.stdout.write("  admin / admin123")
        self.stdout.write("  manager / manager123")
        self.stdout.write("  scale_manager_01 / manager123")
        self.stdout.write("  scale_employee_001 / employee123")

    def _reset_scale_data(self):
        Task.objects.filter(title__startswith="[SCALE]").delete()
        FinanceEntry.objects.filter(description__contains="[SCALE]").delete()
        StockMovement.objects.filter(note__contains="[SCALE]").delete()
        Product.objects.filter(sku__startswith="SCALE-").delete()
        Category.objects.filter(
            name__in=[item[2] for item in PRODUCT_CATALOG],
            products__isnull=True,
        ).delete()
        Employee.objects.filter(employee_id__startswith="SCALE-").delete()
        User.objects.filter(username__startswith="scale_").delete()
        # Keep departments/positions: base demo users may reference them via PROTECT FKs.
        # update_or_create below refreshes them safely without breaking existing data.

    def _ensure_user(self, username, password, role, first_name, last_name):
        user, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "email": f"{username}@nexuserp.local",
                "role": role,
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "is_staff": role == Role.ADMIN,
                "is_superuser": role == Role.ADMIN,
            },
        )
        user.set_password(password)
        user.save()
        return user

    def _seed_structure(self):
        departments = {}
        positions = {}
        for dept_name, titles in DEPARTMENTS.items():
            dept, _ = Department.objects.update_or_create(
                name=dept_name,
                defaults={"description": f"{dept_name} бөліміне арналған масштабты demo дерек", "is_active": True},
            )
            departments[dept_name] = dept
            positions[dept_name] = []
            for idx, title in enumerate(titles, start=1):
                position, _ = Position.objects.update_or_create(
                    title=title,
                    department=dept,
                    defaults={"base_salary": Decimal(250000 + idx * 85000), "is_active": True},
                )
                positions[dept_name].append(position)
        return departments, positions

    def _seed_managers(self, departments, positions, fallback_manager):
        managers = []
        for idx, dept_name in enumerate(DEPARTMENTS.keys(), start=1):
            username = f"scale_manager_{idx:02d}"
            user = self._ensure_user(username, "manager123", Role.MANAGER, dept_name, "Менеджер")
            employee, _ = Employee.objects.update_or_create(
                user=user,
                defaults={
                    "department": departments[dept_name],
                    "position": positions[dept_name][0],
                    "employee_id": f"SCALE-MGR-{idx:02d}",
                    "hire_date": date.today() - timedelta(days=700 + idx * 21),
                    "salary": Decimal(620000 + idx * 40000),
                    "manager": None,
                    "is_active": True,
                },
            )
            managers.append(employee)

        if hasattr(fallback_manager, "employee_profile"):
            managers.append(fallback_manager.employee_profile)
        return managers

    def _ensure_base_manager_profile(self, manager, departments, positions):
        if hasattr(manager, "employee_profile"):
            return manager.employee_profile
        return Employee.objects.create(
            user=manager,
            department=departments["Операциялар"],
            position=positions["Операциялар"][0],
            employee_id="SCALE-MGR-BASE",
            hire_date=date.today() - timedelta(days=900),
            salary=Decimal(650000),
            is_active=True,
        )

    def _seed_employees(self, count, departments, positions, managers):
        first_names = [
            "Аружан",
            "Диас",
            "Айдана",
            "Ернар",
            "Мадина",
            "Нұрсұлтан",
            "Алима",
            "Санжар",
            "Дана",
            "Ерасыл",
            "Назерке",
            "Тимур",
        ]
        last_names = [
            "Серік",
            "Омар",
            "Әли",
            "Нұрлан",
            "Қайрат",
            "Бекзат",
            "Төлеген",
            "Ермек",
        ]
        employees = []
        dept_names = list(DEPARTMENTS.keys())
        for idx in range(1, count + 1):
            dept_name = dept_names[(idx - 1) % len(dept_names)]
            username = f"scale_employee_{idx:03d}"
            user = self._ensure_user(
                username,
                "employee123",
                Role.EMPLOYEE,
                first_names[idx % len(first_names)],
                last_names[idx % len(last_names)],
            )
            employee, _ = Employee.objects.update_or_create(
                user=user,
                defaults={
                    "department": departments[dept_name],
                    "position": random.choice(positions[dept_name][1:] or positions[dept_name]),
                    "employee_id": f"SCALE-EMP-{idx:03d}",
                    "hire_date": date.today() - timedelta(days=random.randint(30, 1200)),
                    "salary": Decimal(random.randrange(260000, 760000, 10000)),
                    "manager": random.choice(managers),
                    "is_active": True,
                },
            )
            employees.append(employee)
        return employees

    def _seed_products(self):
        products = []
        for sku, name, category_name, price, min_stock in PRODUCT_CATALOG:
            category, _ = Category.objects.update_or_create(
                name=category_name,
                defaults={"description": f"{category_name} scale category"},
            )
            product, _ = Product.objects.update_or_create(
                sku=f"SCALE-{sku}",
                defaults={
                    "name": name,
                    "category": category,
                    "quantity": Decimal(random.randint(min_stock + 5, min_stock + 80)),
                    "min_stock_level": Decimal(min_stock),
                    "price": Decimal(price),
                    "is_active": True,
                },
            )
            products.append(product)
        return products

    def _seed_movements(self, count, products, manager):
        for idx in range(1, count + 1):
            product = random.choice(products)
            movement_type = StockMovement.MovementType.IN if idx % 3 != 0 else StockMovement.MovementType.OUT
            quantity = Decimal(random.randint(1, 8))
            if movement_type == StockMovement.MovementType.OUT and product.quantity <= quantity:
                movement_type = StockMovement.MovementType.IN
            movement, created = StockMovement.objects.get_or_create(
                product=product,
                note=f"[SCALE] Қойма қозғалысы #{idx:03d}",
                defaults={
                    "movement_type": movement_type,
                    "quantity": quantity,
                    "unit_price": product.price,
                    "auto_create_finance": False,
                    "created_by": manager,
                },
            )
            if created:
                if movement.movement_type == StockMovement.MovementType.IN:
                    product.quantity += quantity
                else:
                    product.quantity -= quantity
                product.save(update_fields=["quantity", "updated_at"])
            created_at = timezone.now() - timedelta(days=random.randint(1, 180))
            StockMovement.objects.filter(pk=movement.pk).update(created_at=created_at)

    def _seed_finance(self, count, admin, manager):
        for idx in range(1, count + 1):
            is_income = idx % 5 in (0, 1, 2)
            category = random.choice(FINANCE_CATEGORIES)
            base = random.randint(80000, 2500000) if is_income else random.randint(35000, 1200000)
            entry_date = date.today() - timedelta(days=random.randint(1, 365))
            FinanceEntry.objects.get_or_create(
                title=f"[SCALE] {category} {'income' if is_income else 'expense'} #{idx:03d}",
                entry_date=entry_date,
                defaults={
                    "entry_type": FinanceEntry.EntryType.INCOME if is_income else FinanceEntry.EntryType.EXPENSE,
                    "amount": Decimal(base),
                    "category": category,
                    "description": "[SCALE] Realistic finance record for analytics and reports.",
                    "created_by": manager if idx % 2 else admin,
                },
            )

    def _seed_tasks(self, count, employees, managers):
        statuses = [
            Task.Status.ASSIGNED,
            Task.Status.IN_PROGRESS,
            Task.Status.DONE,
            Task.Status.APPROVED,
            Task.Status.REJECTED,
        ]
        priorities = [Task.Priority.LOW, Task.Priority.MEDIUM, Task.Priority.HIGH]
        for idx in range(1, count + 1):
            status = statuses[idx % len(statuses)]
            progress = {
                Task.Status.ASSIGNED: random.choice([0, 5, 10]),
                Task.Status.IN_PROGRESS: random.randint(15, 85),
                Task.Status.DONE: 100,
                Task.Status.APPROVED: 100,
                Task.Status.REJECTED: random.randint(30, 90),
            }[status]
            created_at = timezone.now() - timedelta(days=random.randint(1, 120))
            deadline = timezone.now() + timedelta(days=random.randint(-12, 45))
            manager = random.choice(managers).user
            employee = random.choice(employees)
            task, _ = Task.objects.update_or_create(
                title=f"[SCALE] {random.choice(TASK_TEMPLATES)} #{idx:03d}",
                defaults={
                    "description": (
                        "Масштабты demo үшін жасалған realistic тапсырма. "
                        "Бұл жазба dashboard, workflow, reports және analytics көріністерін толтырады."
                    ),
                    "created_by": manager,
                    "assignee": employee,
                    "status": status,
                    "priority": random.choice(priorities),
                    "deadline": deadline,
                    "progress": progress,
                    "started_at": created_at + timedelta(hours=4) if status != Task.Status.ASSIGNED else None,
                    "submitted_at": created_at + timedelta(days=2) if status in (Task.Status.DONE, Task.Status.APPROVED) else None,
                    "completed_at": created_at + timedelta(days=2) if status in (Task.Status.DONE, Task.Status.APPROVED) else None,
                    "approved_at": created_at + timedelta(days=3) if status == Task.Status.APPROVED else None,
                    "rejected_at": created_at + timedelta(days=3) if status == Task.Status.REJECTED else None,
                    "approval_note": "Жақсы орындалды." if status == Task.Status.APPROVED else "",
                },
            )
            Task.objects.filter(pk=task.pk).update(created_at=created_at, updated_at=created_at)
            TaskActivity.objects.get_or_create(
                task=task,
                action=TaskActivity.Action.CREATED,
                defaults={
                    "actor": manager,
                    "to_status": Task.Status.ASSIGNED,
                    "message": "[SCALE] Тапсырманы менеджер құрды.",
                },
            )
            if status != Task.Status.ASSIGNED:
                TaskActivity.objects.get_or_create(
                    task=task,
                    action=TaskActivity.Action.STATUS_CHANGED,
                    to_status=status,
                    defaults={
                        "actor": employee.user,
                        "from_status": Task.Status.ASSIGNED,
                        "message": f"[SCALE] Workflow moved to {status}.",
                    },
                )
            if idx % 3 == 0:
                TaskComment.objects.get_or_create(
                    task=task,
                    author=employee.user,
                    message="[SCALE] Жұмыс барысы бойынша қысқа update жіберілді.",
                )

    def _seed_notifications(self, employees, managers):
        for idx, employee in enumerate(employees[:40], start=1):
            Notification.objects.get_or_create(
                recipient=employee.user,
                title=f"[SCALE] Notification #{idx:03d}",
                defaults={
                    "actor": random.choice(managers).user,
                    "notification_type": random.choice(
                        [
                            Notification.Type.TASK_ASSIGNED,
                            Notification.Type.DEADLINE,
                            Notification.Type.SYSTEM,
                        ]
                    ),
                    "priority": Notification.Priority.HIGH if idx % 5 == 0 else Notification.Priority.NORMAL,
                    "message": "Масштабты demo хабарлама.",
                    "link": "/dashboard/tasks",
                    "metadata": {"scale": True, "index": idx},
                    "is_read": idx % 4 == 0,
                },
            )
