from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.audit import log_audit_event
from common.rbac import Perm
from common.rbac.drf_permissions import require_any_permission, require_permission
from common.rbac.scope import scope_queryset

from .models import FinanceEntry
from .serializers import FinanceEntrySerializer


class FinanceEntryViewSet(viewsets.ModelViewSet):
    queryset = FinanceEntry.objects.select_related("created_by")
    serializer_class = FinanceEntrySerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ["entry_date", "amount", "created_at"]

    def get_queryset(self):
        return scope_queryset(
            FinanceEntry.objects.select_related("created_by"),
            self.request.user,
            "finance",
        )

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), require_permission(Perm.FINANCE_CREATE)()]
        if self.action in ("update", "partial_update"):
            return [IsAuthenticated(), require_permission(Perm.FINANCE_UPDATE)()]
        if self.action == "destroy":
            return [IsAuthenticated(), require_permission(Perm.FINANCE_DELETE)()]
        if self.action in ("list", "retrieve"):
            return [
                IsAuthenticated(),
                require_any_permission(Perm.FINANCE_VIEW_ALL, Perm.FINANCE_VIEW_DEPARTMENT)(),
            ]
        return super().get_permissions()

    def perform_create(self, serializer):
        entry = serializer.save(created_by=self.request.user)
        log_audit_event(
            request=self.request,
            action="create",
            resource_type="finance",
            resource_id=entry.id,
            message=entry.title,
        )

    def perform_update(self, serializer):
        entry = serializer.save()
        log_audit_event(
            request=self.request,
            action="update",
            resource_type="finance",
            resource_id=entry.id,
            message=entry.title,
        )

    def perform_destroy(self, instance):
        log_audit_event(
            request=self.request,
            action="delete",
            resource_type="finance",
            resource_id=instance.id,
            message=instance.title,
        )
        super().perform_destroy(instance)
