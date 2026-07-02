from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.employees.models import Department, Employee, Position


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def org():
    sales = Department.objects.create(name="Сату", description="Сату бөлімі")
    it = Department.objects.create(name="IT", description="IT бөлімі")
    sales_manager_pos = Position.objects.create(
        title="Менеджер",
        department=sales,
        base_salary=Decimal("650000"),
    )
    sales_employee_pos = Position.objects.create(
        title="Сату маманы",
        department=sales,
        base_salary=Decimal("350000"),
    )
    it_manager_pos = Position.objects.create(
        title="IT менеджер",
        department=it,
        base_salary=Decimal("700000"),
    )
    it_employee_pos = Position.objects.create(
        title="Инженер",
        department=it,
        base_salary=Decimal("380000"),
    )
    return {
        "sales": sales,
        "it": it,
        "sales_manager_pos": sales_manager_pos,
        "sales_employee_pos": sales_employee_pos,
        "it_manager_pos": it_manager_pos,
        "it_employee_pos": it_employee_pos,
    }


def _make_user(username: str, role: str) -> User:
    return User.objects.create_user(
        username=username,
        email=f"{username}@test.local",
        password="pass1234",
        role=role,
    )


@pytest.fixture
def admin_user():
    return _make_user("admin_test", Role.ADMIN)


@pytest.fixture
def sales_manager(org):
    user = _make_user("sales_manager", Role.MANAGER)
    employee = Employee.objects.create(
        user=user,
        department=org["sales"],
        position=org["sales_manager_pos"],
        employee_id="MGR-SALES-001",
        hire_date=date(2024, 1, 10),
        salary=Decimal("650000"),
    )
    return user, employee


@pytest.fixture
def it_manager(org):
    user = _make_user("it_manager", Role.MANAGER)
    employee = Employee.objects.create(
        user=user,
        department=org["it"],
        position=org["it_manager_pos"],
        employee_id="MGR-IT-001",
        hire_date=date(2024, 1, 11),
        salary=Decimal("700000"),
    )
    return user, employee


@pytest.fixture
def sales_employee(org, sales_manager):
    user = _make_user("sales_emp", Role.EMPLOYEE)
    employee = Employee.objects.create(
        user=user,
        department=org["sales"],
        position=org["sales_employee_pos"],
        employee_id="EMP-SALES-001",
        hire_date=date(2024, 2, 10),
        salary=Decimal("320000"),
        manager=sales_manager[1],
    )
    return user, employee


@pytest.fixture
def it_employee(org, it_manager):
    user = _make_user("it_emp", Role.EMPLOYEE)
    employee = Employee.objects.create(
        user=user,
        department=org["it"],
        position=org["it_employee_pos"],
        employee_id="EMP-IT-001",
        hire_date=date(2024, 2, 12),
        salary=Decimal("340000"),
        manager=it_manager[1],
    )
    return user, employee
