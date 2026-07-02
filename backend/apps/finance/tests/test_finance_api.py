from datetime import date
from decimal import Decimal

import pytest
from rest_framework import status

from apps.finance.models import FinanceEntry


@pytest.mark.django_db
def test_manager_sees_only_department_finance_entries(api_client, sales_manager, it_manager):
    sales_user, _ = sales_manager
    it_user, _ = it_manager
    own = FinanceEntry.objects.create(
        entry_type=FinanceEntry.EntryType.INCOME,
        title="Сату кірісі",
        amount=Decimal("100000"),
        category="Сату",
        entry_date=date.today(),
        created_by=sales_user,
    )
    FinanceEntry.objects.create(
        entry_type=FinanceEntry.EntryType.EXPENSE,
        title="IT шығыны",
        amount=Decimal("50000"),
        category="IT",
        entry_date=date.today(),
        created_by=it_user,
    )

    api_client.force_authenticate(sales_user)
    response = api_client.get("/api/v1/finance/entries/")
    assert response.status_code == status.HTTP_200_OK
    ids = [row["id"] for row in response.data["results"]]
    assert ids == [own.id]


@pytest.mark.django_db
def test_finance_create_sets_created_by(api_client, sales_manager):
    sales_user, _ = sales_manager
    api_client.force_authenticate(sales_user)
    response = api_client.post(
        "/api/v1/finance/entries/",
        {
            "entry_type": "income",
            "title": "Жаңа табыс",
            "amount": "77777",
            "category": "Сату",
            "description": "Тест",
            "entry_date": str(date.today()),
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    created = FinanceEntry.objects.get(id=response.data["id"])
    assert created.created_by_id == sales_user.id
