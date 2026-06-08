from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F


@shared_task(name="notifications.send_email")
def send_email_task(subject: str, message: str, recipient_list: list[str]):
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )


@shared_task(name="notifications.check_low_stock")
def check_low_stock_task():
    from apps.warehouse.models import Product

    low_stock = Product.objects.filter(is_active=True, quantity__lte=F("min_stock_level"))
    return {"alerted": low_stock.count()}


@shared_task(name="notifications.bulk_email")
def send_bulk_email_task(subject: str, message: str, role: str | None = None):
    from apps.accounts.models import User

    users = User.objects.filter(is_active=True).exclude(email="")
    if role:
        users = users.filter(role=role)
    recipient_list = list(users.values_list("email", flat=True))
    if not recipient_list:
        return {"sent": 0, "role": role, "status": "no_recipients"}

    sent = send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )
    return {"sent": sent, "recipients": len(recipient_list), "role": role}
