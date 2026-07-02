from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        TASK_ASSIGNED = "task_assigned", "Тапсырма берілді"
        TASK_STARTED = "task_started", "Тапсырма басталды"
        TASK_SUBMITTED = "task_submitted", "Тексеруге жіберілді"
        TASK_APPROVED = "task_approved", "Тапсырма бекітілді"
        TASK_REJECTED = "task_rejected", "Тапсырма қайтарылды"
        TASK_COMMENT = "task_comment", "Тапсырма пікірі"
        DEADLINE = "deadline", "Мерзім"
        LOW_STOCK = "low_stock", "Төмен қор"
        SYSTEM = "system", "Жүйе"

    class Priority(models.TextChoices):
        LOW = "low", "Төмен"
        NORMAL = "normal", "Қалыпты"
        HIGH = "high", "Жоғары"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    notification_type = models.CharField(max_length=32, choices=Type.choices, db_index=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient}: {self.title}"
