from rest_framework import viewsets

from common.permissions import IsManagerOrAdmin

from .models import FinanceEntry
from .serializers import FinanceEntrySerializer


class FinanceEntryViewSet(viewsets.ModelViewSet):
    queryset = FinanceEntry.objects.select_related("created_by")
    serializer_class = FinanceEntrySerializer
    permission_classes = [IsManagerOrAdmin]
    ordering_fields = ["entry_date", "amount", "created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
