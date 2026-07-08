import pytest
from rest_framework import status

from apps.accounts.models import Role
from apps.employees.models import Department


@pytest.mark.django_db
def test_employee_cannot_list_other_employees(api_client, sales_employee):
    user, _ = sales_employee
    api_client.force_authenticate(user)
    response = api_client.get("/api/v1/employees/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_manager_cannot_create_employee(api_client, sales_manager):
    manager_user, manager_emp = sales_manager
    api_client.force_authenticate(manager_user)
    payload = {
        "username": "new_emp",
        "email": "new@test.local",
        "password": "Str0ngPass!123",
        "employee_id": "EMP-NEW-001",
        "department": manager_emp.department_id,
        "position": manager_emp.position_id,
        "hire_date": "2024-03-01",
        "salary": "300000",
    }
    response = api_client.post("/api/v1/employees/", payload, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_manager_cannot_create_department(api_client, sales_manager):
    manager_user, _ = sales_manager
    api_client.force_authenticate(manager_user)
    response = api_client.post(
        "/api/v1/employees/departments/",
        {"name": "Жаңа бөлім", "description": "test"},
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_promote_employee_to_manager(api_client, admin_user, sales_employee, org):
    api_client.force_authenticate(admin_user)
    employee_user, employee = sales_employee
    response = api_client.post(
        f"/api/v1/employees/{employee.id}/promote/",
        {"department": org["sales"].id},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    employee_user.refresh_from_db()
    assert employee_user.role == Role.MANAGER
    org["sales"].refresh_from_db()
    dept = Department.objects.get(id=org["sales"].id)
    assert dept.manager_id == employee.id


@pytest.mark.django_db
def test_admin_can_block_employee(api_client, admin_user, sales_employee):
    api_client.force_authenticate(admin_user)
    employee_user, employee = sales_employee
    response = api_client.post(f"/api/v1/employees/{employee.id}/block/")
    assert response.status_code == status.HTTP_200_OK
    employee_user.refresh_from_db()
    assert employee_user.is_active is False


@pytest.mark.django_db
def test_employee_cannot_access_analytics(api_client, sales_employee):
    user, _ = sales_employee
    api_client.force_authenticate(user)
    response = api_client.get("/api/v1/analytics/dashboard/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_transfer_employee(api_client, admin_user, sales_employee, org):
    api_client.force_authenticate(admin_user)
    employee_user, employee = sales_employee
    response = api_client.post(
        f"/api/v1/employees/{employee.id}/transfer/",
        {
            "department": org["it"].id,
            "position": org["it_employee_pos"].id,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    employee.refresh_from_db()
    assert employee.department_id == org["it"].id


@pytest.mark.django_db
def test_auth_me_returns_permissions(api_client, admin_user):
    api_client.force_authenticate(admin_user)
    response = api_client.get("/api/v1/auth/me/")
    assert response.status_code == status.HTTP_200_OK
    assert "permissions" in response.data
    assert "employees.create" in response.data["permissions"]
    assert response.data["scope"]["role"] == "admin"
