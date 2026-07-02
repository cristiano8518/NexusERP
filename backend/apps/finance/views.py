from rest_framework import viewsets

from common.permissions import IsManagerOrAdmin

from .models import FinanceEntry
from .serializers import FinanceEntrySerializer


class FinanceEntryViewSet(viewsets.ModelViewSet):
    queryset = FinanceEntry.objects.select_related("created_by")
    serializer_class = FinanceEntrySerializer
    permission_classes = [IsManagerOrAdmin]
    ordering_fields = ["entry_date", "amount", "created_at"]

    def get_queryset(self):
        user = self.request.user
        qs = FinanceEntry.objects.select_related("created_by")
        if getattr(user, "role", None) == "admin":
            return qs
        if getattr(user, "role", None) == "manager" and hasattr(user, "employee_profile"):
            return qs.filter(created_by__employee_profile__department_id=user.employee_profile.department_id)
        return qs.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
