from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.username", read_only=True)
    type_display = serializers.CharField(source="get_notification_type_display", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "actor",
            "actor_name",
            "notification_type",
            "type_display",
            "priority",
            "title",
            "message",
            "link",
            "metadata",
            "is_read",
            "read_at",
            "created_at",
        )
        read_only_fields = fields
