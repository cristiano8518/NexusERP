from django.contrib.auth import get_user_model

from .models import Notification, NotificationPreference

User = get_user_model()


def _should_notify(recipient, notification_type: str, channel: str = "in_app") -> bool:
    prefs = NotificationPreference.objects.filter(user=recipient).first()
    if not prefs:
        return True
    if notification_type in (prefs.muted_types or []):
        return False
    if channel == "email":
        return prefs.email_enabled
    return prefs.in_app_enabled


def get_or_create_preferences(user):
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    return prefs


def create_notification(
    *,
    recipient,
    notification_type: str,
    title: str,
    message: str = "",
    actor=None,
    link: str = "",
    priority: str = Notification.Priority.NORMAL,
    metadata: dict | None = None,
) -> Notification | None:
    if not recipient:
        return None
    if not _should_notify(recipient, notification_type, channel="in_app"):
        return None
    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        priority=priority,
        title=title,
        message=message,
        link=link,
        metadata=metadata or {},
    )


def notify_role(
    *,
    role: str,
    notification_type: str,
    title: str,
    message: str = "",
    actor=None,
    link: str = "",
    priority: str = Notification.Priority.NORMAL,
    metadata: dict | None = None,
):
    users = User.objects.filter(role=role, is_active=True)
    return [
        create_notification(
            recipient=user,
            actor=actor,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link,
            priority=priority,
            metadata=metadata,
        )
        for user in users
    ]
