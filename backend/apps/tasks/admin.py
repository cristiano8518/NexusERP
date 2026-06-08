from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Task, TaskActivity, TaskComment


class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    readonly_fields = ("author", "message", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class TaskActivityInline(admin.TabularInline):
    model = TaskActivity
    extra = 0
    readonly_fields = (
        "actor",
        "action",
        "from_status",
        "to_status",
        "message",
        "created_at",
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "priority",
        "assignee",
        "deadline",
        "created_at",
        "admin_actions",
    )
    list_filter = ("status", "priority", "created_at")
    search_fields = ("title", "description")
    raw_id_fields = ("created_by", "assignee")
    date_hierarchy = "created_at"
    inlines = [TaskCommentInline, TaskActivityInline]

    @admin.display(description="Әрекеттер")
    def admin_actions(self, obj):
        change_url = reverse("admin:tasks_task_change", args=[obj.pk])
        delete_url = reverse("admin:tasks_task_delete", args=[obj.pk])
        return format_html(
            '<span class="nexuserp-actions">'
            '<a href="{}">Өңдеу</a> '
            '<a class="deletelink" href="{}">Өшіру</a>'
            "</span>",
            change_url,
            delete_url,
        )


@admin.register(TaskActivity)
class TaskActivityAdmin(admin.ModelAdmin):
    list_display = ("task", "actor", "action", "from_status", "to_status", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("task__title", "actor__username", "message")
    readonly_fields = ("task", "actor", "action", "from_status", "to_status", "message", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "created_at")
    search_fields = ("task__title", "author__username", "message")
    readonly_fields = ("task", "author", "message", "created_at")
