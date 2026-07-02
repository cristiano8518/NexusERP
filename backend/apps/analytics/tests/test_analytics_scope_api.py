from decimal import Decimal

import pytest
from rest_framework import status

from apps.warehouse.models import Category, Product, StockMovement


@pytest.mark.django_db
def test_manager_dashboard_warehouse_stats_are_department_scoped(api_client, sales_manager, it_manager):
    sales_user, _ = sales_manager
    it_user, _ = it_manager
    category = Category.objects.create(name="Склад тест")
    sales_product = Product.objects.create(
        sku="AN-SALES-1",
        name="Sales Product",
        category=category,
        quantity=Decimal("1"),
        min_stock_level=Decimal("2"),
        price=Decimal("100"),
    )
    it_product = Product.objects.create(
        sku="AN-IT-1",
        name="IT Product",
        category=category,
        quantity=Decimal("10"),
        min_stock_level=Decimal("2"),
        price=Decimal("100"),
    )
    StockMovement.objects.create(
        product=sales_product,
        movement_type=StockMovement.MovementType.IN,
        quantity=Decimal("1"),
        unit_price=Decimal("100"),
        created_by=sales_user,
    )
    StockMovement.objects.create(
        product=it_product,
        movement_type=StockMovement.MovementType.IN,
        quantity=Decimal("1"),
        unit_price=Decimal("100"),
        created_by=it_user,
    )

    api_client.force_authenticate(sales_user)
    response = api_client.get("/api/v1/analytics/dashboard/")
    assert response.status_code == status.HTTP_200_OK
    warehouse = response.data["data"]["warehouse"]
    assert warehouse["products"] == 1
    assert warehouse["low_stock"] == 1
