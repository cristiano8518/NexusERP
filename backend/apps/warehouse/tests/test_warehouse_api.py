from decimal import Decimal

import pytest
from rest_framework import status

from apps.finance.models import FinanceEntry
from apps.warehouse.models import Category, Product


@pytest.mark.django_db
def test_stock_out_fails_if_not_enough_quantity(api_client, sales_manager):
    manager_user, _ = sales_manager
    category = Category.objects.create(name="Жабдық")
    product = Product.objects.create(
        sku="SKU-LOW-1",
        name="Ноутбук",
        category=category,
        quantity=Decimal("2"),
        min_stock_level=Decimal("1"),
        price=Decimal("1000"),
    )
    api_client.force_authenticate(manager_user)
    response = api_client.post(
        "/api/v1/warehouse/movements/",
        {
            "product": product.id,
            "movement_type": "out",
            "quantity": "5",
            "unit_price": "1000",
            "note": "Тест шығыс",
            "auto_create_finance": True,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "errors" in response.data
    assert "quantity" in response.data["errors"]


@pytest.mark.django_db
def test_stock_in_creates_finance_entry_and_updates_quantity(api_client, sales_manager):
    manager_user, _ = sales_manager
    category = Category.objects.create(name="Кеңсе")
    product = Product.objects.create(
        sku="SKU-IN-1",
        name="Принтер",
        category=category,
        quantity=Decimal("3"),
        min_stock_level=Decimal("2"),
        price=Decimal("500"),
    )
    api_client.force_authenticate(manager_user)
    response = api_client.post(
        "/api/v1/warehouse/movements/",
        {
            "product": product.id,
            "movement_type": "in",
            "quantity": "4",
            "unit_price": "500",
            "note": "Кіріс партиясы",
            "auto_create_finance": True,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    product.refresh_from_db()
    assert product.quantity == Decimal("7")
    finance = FinanceEntry.objects.get(stock_movement__id=response.data["id"])
    assert finance.category == "Қойма"
