import hashlib
import hmac
import json
import time

import pytest
from django.core.cache import cache
from rest_framework import status

from apps.integrations.services import ExternalAPIError


@pytest.mark.django_db
def test_integrations_status_admin_only(api_client, admin_user, sales_manager):
    manager_user, _ = sales_manager
    api_client.force_authenticate(manager_user)
    denied = api_client.get("/api/v1/integrations/status/")
    assert denied.status_code == status.HTTP_403_FORBIDDEN

    api_client.force_authenticate(admin_user)
    allowed = api_client.get("/api/v1/integrations/status/")
    assert allowed.status_code == status.HTTP_200_OK
    assert "integrations" in allowed.data


@pytest.mark.django_db
def test_external_employees_get_handles_upstream_error(api_client, sales_manager, monkeypatch):
    manager_user, _ = sales_manager

    def _raise():
        raise ExternalAPIError("upstream timeout")

    monkeypatch.setattr("apps.integrations.urls.fetch_external_employees", _raise)
    api_client.force_authenticate(manager_user)
    response = api_client.get("/api/v1/integrations/external-employees/")
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert response.data["success"] is False


@pytest.mark.django_db
def test_webhook_signature_and_cache(api_client, settings):
    settings.EXTERNAL_WEBHOOK_SECRET = "dev-webhook-secret"
    bad = api_client.post(
        "/api/v1/integrations/webhooks/external/",
        {"event": "employee.updated", "payload": {"id": 1}},
        format="json",
        HTTP_X_NEXUS_SIGNATURE="wrong",
    )
    assert bad.status_code == status.HTTP_403_FORBIDDEN

    payload = {"event": "employee.updated", "payload": {"id": 1, "name": "A"}}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ts = str(int(time.time()))
    sign = "sha256=" + hmac.new(
        settings.EXTERNAL_WEBHOOK_SECRET.encode("utf-8"),
        f"{ts}.".encode() + raw,
        hashlib.sha256,
    ).hexdigest()
    ok = api_client.post(
        "/api/v1/integrations/webhooks/external/",
        payload,
        format="json",
        HTTP_X_NEXUS_SIGNATURE=sign,
        HTTP_X_NEXUS_TIMESTAMP=ts,
    )
    assert ok.status_code == status.HTTP_202_ACCEPTED
    cached = cache.get("integrations:webhook:last:employee.updated")
    assert cached["payload"]["id"] == 1
