from .models import SecurityLog, User


def get_client_ip(request) -> str | None:
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_security_event(
    request,
    event_type: str,
    user: User | None = None,
    metadata: dict | None = None,
) -> SecurityLog:
    return SecurityLog.objects.create(
        user=user,
        event_type=event_type,
        ip_address=get_client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:512],
        metadata=metadata or {},
    )
