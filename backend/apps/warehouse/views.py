from django.db import transaction
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.finance.models import FinanceEntry
from apps.notifications.models import Notification
from apps.notifications.services import notify_role
from common.audit import log_audit_event
from common.rbac import Perm
from common.rbac.checker import PermissionChecker
from common.rbac.drf_permissions import require_any_permission, require_permission
from common.rbac.scope import scope_queryset

from .models import Category, Product, StockMovement
from .serializers import CategorySerializer, ProductSerializer, StockMovementSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, require_permission(Perm.WAREHOUSE_MANAGE)]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [
                IsAuthenticated(),
                require_any_permission(Perm.WAREHOUSE_VIEW_ALL, Perm.WAREHOUSE_VIEW_DEPARTMENT)(),
            ]
        return [IsAuthenticated(), require_permission(Perm.WAREHOUSE_MANAGE)()]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").prefetch_related("movements")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "sku"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [
                IsAuthenticated(),
                require_any_permission(Perm.WAREHOUSE_VIEW_ALL, Perm.WAREHOUSE_VIEW_DEPARTMENT)(),
            ]
        return [IsAuthenticated(), require_permission(Perm.WAREHOUSE_MANAGE)()]


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related("product", "created_by")
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return scope_queryset(
            StockMovement.objects.select_related("product", "created_by"),
            self.request.user,
            "warehouse_movements",
        )

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [
                IsAuthenticated(),
                require_any_permission(Perm.WAREHOUSE_VIEW_ALL, Perm.WAREHOUSE_VIEW_DEPARTMENT)(),
            ]
        return [IsAuthenticated(), require_permission(Perm.WAREHOUSE_MANAGE)()]

    def perform_create(self, serializer):
        with transaction.atomic():
            movement = serializer.save(created_by=self.request.user)
            product = Product.objects.select_for_update().get(pk=movement.product_id)
            if movement.movement_type == StockMovement.MovementType.IN:
                product.quantity += movement.quantity
            else:
                if product.quantity < movement.quantity:
                    raise ValidationError({"quantity": "Қоймада жеткілікті тауар жоқ."})
                product.quantity -= movement.quantity
            product.save(update_fields=["quantity", "updated_at"])

            if movement.auto_create_finance and movement.total_amount > 0:
                entry_type = (
                    FinanceEntry.EntryType.EXPENSE
                    if movement.movement_type == StockMovement.MovementType.IN
                    else FinanceEntry.EntryType.INCOME
                )
                title_prefix = "Қойма кірісі" if movement.movement_type == StockMovement.MovementType.IN else "Қойма шығысы"
                finance_entry = FinanceEntry.objects.create(
                    entry_type=entry_type,
                    title=f"{title_prefix}: {product.name}",
                    amount=movement.total_amount,
                    category="Қойма",
                    description=movement.note or f"Қойма қозғалысы #{movement.id}",
                    entry_date=movement.created_at.date(),
                    created_by=self.request.user,
                )
                movement.finance_entry = finance_entry
                movement.save(update_fields=["finance_entry"])

        if product.is_low_stock:
            notify_role(
                role="manager",
                actor=self.request.user,
                notification_type=Notification.Type.LOW_STOCK,
                priority=Notification.Priority.HIGH,
                title=f"Қор төмен: {product.name}",
                message=f"Қалдық: {product.quantity} {product.unit}. Минимум: {product.min_stock_level}",
                link="/dashboard/warehouse",
                metadata={"product_id": product.id},
            )
        log_audit_event(
            request=self.request,
            action="create",
            resource_type="stock_movement",
            resource_id=movement.id,
            message=f"{product.name}: {movement.movement_type}",
        )
