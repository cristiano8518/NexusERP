from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.rbac import Perm
from common.rbac.checker import PermissionChecker

from .models import Notification
from .serializers import NotificationPreferenceSerializer, NotificationSerializer
from .services import get_or_create_preferences
from .tasks import send_bulk_email_task


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.select_related("actor").filter(
            recipient=self.request.user
        )
        only_unread = self.request.query_params.get("unread")
        if only_unread in ("1", "true", "yes"):
            queryset = queryset.filter(is_read=False)
        return queryset

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"success": True, "count": count})

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now(),
        )
        return Response({"success": True, "updated": updated})

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        return Response(
            {"success": True, "notification": self.get_serializer(notification).data},
            status=status.HTTP_200_OK,
        )


class BulkEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not PermissionChecker(request.user).has(Perm.NOTIFICATIONS_BULK_EMAIL):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Рұқсат жеткіліксіз.")
        subject = (request.data.get("subject") or "").strip()
        message = (request.data.get("message") or "").strip()
        role = request.data.get("role")
        if not subject or not message:
            return Response(
                {"success": False, "detail": "subject and message are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if role not in (None, "", "admin", "manager", "employee"):
            return Response(
                {"success": False, "detail": "role must be admin, manager, employee or empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        async_result = send_bulk_email_task.delay(subject, message, role or None)
        return Response(
            {
                "success": True,
                "task_id": async_result.id,
                "message": "Bulk email started in background.",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class NotificationPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prefs = get_or_create_preferences(request.user)
        return Response(
            {"success": True, "preferences": NotificationPreferenceSerializer(prefs).data}
        )

    def patch(self, request):
        prefs = get_or_create_preferences(request.user)
        serializer = NotificationPreferenceSerializer(prefs, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "preferences": serializer.data})
