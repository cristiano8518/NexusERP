"""Persistent business audit trail."""

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Жасалды"
        UPDATE = "update", "Жаңартылды"
        DELETE = "delete", "Жойылды"
        TRANSFER = "transfer", "Ауыстырылды"
        PROMOTE = "promote", "Көтерілді"
        DEMOTE = "demote", "Түсірілді"
        BLOCK = "block", "Блокталды"
        UNBLOCK = "unblock", "Блоктан шығарылды"
        UPLOAD = "upload", "Жүктелді"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=32, choices=Action.choices, db_index=True)
    resource_type = models.CharField(max_length=64, db_index=True)
    resource_id = models.CharField(max_length=64, blank=True, db_index=True)
    message = models.TextField(blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "audit log"
        verbose_name_plural = "audit logs"

    def __str__(self):
        return f"{self.action} {self.resource_type}:{self.resource_id}"
