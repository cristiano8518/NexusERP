from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "recipient",
        "actor",
        "notification_type",
        "priority",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "priority", "is_read", "created_at")
    search_fields = ("title", "message", "recipient__username", "actor__username")
    readonly_fields = (
        "recipient",
        "actor",
        "notification_type",
        "priority",
        "title",
        "message",
        "link",
        "metadata",
        "is_read",
        "read_at",
        "created_at",
    )
