from django.apps import apps


def log_audit_event(
    *,
    request=None,
    actor=None,
    action: str,
    resource_type: str,
    resource_id="",
    message: str = "",
    changes: dict | None = None,
):
    AuditLog = apps.get_model("accounts", "AuditLog")
    if actor is None and request is not None:
        actor = getattr(request, "user", None)
        if actor and not actor.is_authenticated:
            actor = None

    ip_address = None
    if request is not None:
        ip_address = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get(
            "REMOTE_ADDR"
        )

    AuditLog.objects.create(
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else "",
        message=message,
        changes=changes or {},
        ip_address=ip_address or None,
    )
