import hmac
import hashlib
import time

from django.conf import settings
from django.core.cache import cache
from django.urls import path
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from common.permissions import IsAdminRole, IsManagerOrAdmin
from .services import ExternalAPIError, fetch_external_employees
from .tasks import sync_external_employees_task


class IntegrationsStatusView(APIView):
    """Runtime status for external integrations."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        return Response(
            {
                "success": True,
                "integrations": {
                    "odoo": {
                        "enabled": bool(getattr(settings, "ODOO_EMPLOYEES_URL", "")),
                        "status": "configured" if getattr(settings, "ODOO_EMPLOYEES_URL", "") else "mock_mode",
                    },
                    "webhooks": {
                        "enabled": bool(getattr(settings, "EXTERNAL_WEBHOOK_SECRET", "")),
                        "status": "ready",
                    },
                    "telegram": {"enabled": False, "status": "not_configured"},
                },
            }
        )


class ExternalEmployeesSyncView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        try:
            payload = fetch_external_employees()
        except ExternalAPIError as exc:
            return Response({"success": False, "detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({"success": True, "data": payload})

    def post(self, request):
        async_result = sync_external_employees_task.delay()
        return Response(
            {
                "success": True,
                "task_id": async_result.id,
                "message": "External employee sync started in background.",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ExternalWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        secret = getattr(settings, "EXTERNAL_WEBHOOK_SECRET", "")
        signature = request.headers.get("X-Nexus-Signature", "")
        timestamp = request.headers.get("X-Nexus-Timestamp", "")
        if secret:
            if not timestamp:
                return Response({"success": False, "detail": "Missing webhook timestamp."}, status=403)
            try:
                ts_int = int(timestamp)
            except ValueError:
                return Response({"success": False, "detail": "Invalid webhook timestamp."}, status=403)
            if abs(int(time.time()) - ts_int) > 300:
                return Response({"success": False, "detail": "Webhook timestamp expired."}, status=403)

            # Replay protection: identical signature+timestamp can be used only once.
            replay_key = f"integrations:webhook:seen:{timestamp}:{signature}"
            if cache.get(replay_key):
                return Response({"success": False, "detail": "Webhook replay detected."}, status=403)

            body = request.body or b""
            digest = hmac.new(
                secret.encode("utf-8"),
                f"{timestamp}.".encode("utf-8") + body,
                hashlib.sha256,
            ).hexdigest()
            expected = f"sha256={digest}"
            if not hmac.compare_digest(signature, expected):
                return Response({"success": False, "detail": "Invalid webhook signature."}, status=403)
            cache.set(replay_key, True, 600)

        event_type = request.data.get("event", "unknown")
        payload = request.data.get("payload", {})
        cache_key = f"integrations:webhook:last:{event_type}"
        cache.set(cache_key, {"event": event_type, "payload": payload}, 3600)
        return Response(
            {
                "success": True,
                "event": event_type,
                "processed": True,
                "cache_key": cache_key,
                "payload_keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
            },
            status=status.HTTP_202_ACCEPTED,
        )


urlpatterns = [
    path("integrations/status/", IntegrationsStatusView.as_view(), name="integrations-status"),
    path("integrations/external-employees/", ExternalEmployeesSyncView.as_view(), name="integrations-external-employees"),
    path("integrations/webhooks/external/", ExternalWebhookView.as_view(), name="integrations-external-webhook"),
]
