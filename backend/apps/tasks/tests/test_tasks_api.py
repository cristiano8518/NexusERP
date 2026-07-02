from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from apps.tasks.models import Task


@pytest.mark.django_db
def test_manager_list_tasks_only_own_department(api_client, sales_manager, sales_employee, it_employee):
    manager_user, _ = sales_manager
    own_task = Task.objects.create(
        title="Өз бөлім тапсырмасы",
        created_by=manager_user,
        assignee=sales_employee[1],
        status=Task.Status.ASSIGNED,
    )
    Task.objects.create(
        title="Басқа бөлім тапсырмасы",
        created_by=manager_user,
        assignee=it_employee[1],
        status=Task.Status.ASSIGNED,
    )

    api_client.force_authenticate(manager_user)
    response = api_client.get("/api/v1/tasks/")
    assert response.status_code == status.HTTP_200_OK
    ids = [item["id"] for item in response.data["results"]]
    assert own_task.id in ids
    assert len(ids) == 1


@pytest.mark.django_db
def test_manager_cannot_assign_task_outside_department(api_client, sales_manager, it_employee):
    manager_user, _ = sales_manager
    api_client.force_authenticate(manager_user)

    payload = {
        "title": "Кросс-бөлім тапсырмасы",
        "description": "Тест",
        "priority": Task.Priority.MEDIUM,
        "assignee": it_employee[1].id,
        "deadline": (timezone.now() + timedelta(days=2)).isoformat(),
    }
    response = api_client.post("/api/v1/tasks/", payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "errors" in response.data
    assert "assignee" in response.data["errors"]


@pytest.mark.django_db
def test_employee_can_only_update_progress(api_client, sales_employee, sales_manager):
    manager_user, _ = sales_manager
    employee_user, employee = sales_employee
    task = Task.objects.create(
        title="Тапсырма",
        created_by=manager_user,
        assignee=employee,
        status=Task.Status.IN_PROGRESS,
        progress=5,
    )

    api_client.force_authenticate(employee_user)
    response = api_client.patch(
        f"/api/v1/tasks/{task.id}/",
        {"progress": 45, "title": "Өзгертпеу керек"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    task.refresh_from_db()
    assert task.progress == 45
    assert task.title == "Тапсырма"


@pytest.mark.django_db
def test_employee_cannot_approve_task(api_client, sales_employee, sales_manager):
    manager_user, _ = sales_manager
    employee_user, employee = sales_employee
    task = Task.objects.create(
        title="Approval тесті",
        created_by=manager_user,
        assignee=employee,
        status=Task.Status.DONE,
    )

    api_client.force_authenticate(employee_user)
    response = api_client.post(
        f"/api/v1/tasks/{task.id}/transition/",
        {"status": Task.Status.APPROVED},
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_manager_can_approve_done_task_from_own_department(api_client, sales_manager, sales_employee):
    manager_user, _ = sales_manager
    task = Task.objects.create(
        title="Менеджер approval",
        created_by=manager_user,
        assignee=sales_employee[1],
        status=Task.Status.DONE,
        progress=100,
    )

    api_client.force_authenticate(manager_user)
    response = api_client.post(
        f"/api/v1/tasks/{task.id}/transition/",
        {"status": Task.Status.APPROVED, "note": "OK"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    task.refresh_from_db()
    assert task.status == Task.Status.APPROVED
