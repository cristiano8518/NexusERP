import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("nexuserp")


class ExternalAPIError(Exception):
    pass


def fetch_external_employees():
    """Fetch employees from an Odoo-compatible/mock HTTP API with timeout handling."""
    url = getattr(settings, "ODOO_EMPLOYEES_URL", "")
    timeout = getattr(settings, "EXTERNAL_API_TIMEOUT_SECONDS", 5)
    if not url:
        return {
            "source": "mock",
            "employees": [
                {"external_id": "odoo-001", "name": "Demo Odoo Manager", "email": "odoo.manager@example.com"},
                {"external_id": "odoo-002", "name": "Demo Odoo Employee", "email": "odoo.employee@example.com"},
            ],
        }

    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status >= 500:
                raise ExternalAPIError(f"External API server error: {response.status}")
            payload = json.loads(response.read().decode("utf-8"))
            return {"source": url, "employees": payload.get("employees", payload)}
    except urllib.error.URLError as exc:
        logger.warning("External employee API failed: %s", exc)
        raise ExternalAPIError(f"External API unavailable: {exc}") from exc
    except TimeoutError as exc:
        logger.warning("External employee API timeout: %s", exc)
        raise ExternalAPIError("External API timeout") from exc


def cache_external_employees():
    payload = fetch_external_employees()
    cache.set("integrations:external_employees", payload, 300)
    return payload
