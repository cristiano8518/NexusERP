from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


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
