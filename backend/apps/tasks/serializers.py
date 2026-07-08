from rest_framework import serializers

from .models import Task, TaskActivity, TaskAttachment, TaskComment


class TaskAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source="uploaded_by.username", read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = TaskAttachment
        fields = (
            "id",
            "file",
            "file_url",
            "original_name",
            "size",
            "uploaded_by",
            "uploaded_by_name",
            "created_at",
        )
        read_only_fields = ("id", "uploaded_by", "uploaded_by_name", "created_at", "size", "original_name")

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None


class TaskActivitySerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.username", read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = TaskActivity
        fields = (
            "id",
            "actor",
            "actor_name",
            "action",
            "action_display",
            "from_status",
            "to_status",
            "message",
            "created_at",
        )
        read_only_fields = fields


class TaskCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = TaskComment
        fields = ("id", "author", "author_name", "message", "created_at")
        read_only_fields = ("id", "author", "author_name", "created_at")


class TaskSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    assignee_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "status",
            "status_display",
            "priority",
            "priority_display",
            "created_by",
            "created_by_name",
            "assignee",
            "assignee_name",
            "deadline",
            "progress",
            "started_at",
            "submitted_at",
            "completed_at",
            "approved_at",
            "rejected_at",
            "approval_note",
            "is_overdue",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_by",
            "status_display",
            "priority_display",
            "started_at",
            "submitted_at",
            "completed_at",
            "approved_at",
            "rejected_at",
            "is_overdue",
            "created_at",
            "updated_at",
        )

    def get_assignee_name(self, obj):
        if obj.assignee:
            return str(obj.assignee)
        return None

    def validate_progress(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Прогресс 0 мен 100 аралығында болуы керек.")
        return value


class TaskDetailSerializer(TaskSerializer):
    comments = TaskCommentSerializer(many=True, read_only=True)
    activities = TaskActivitySerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ("comments", "activities", "attachments")
