from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.employees.models import Employee


class Task(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Жоба"
        ASSIGNED = "assigned", "Тапсырылды"
        IN_PROGRESS = "in_progress", "Орындалуда"
        DONE = "done", "Аяқталды"
        APPROVED = "approved", "Бекітілді"
        REJECTED = "rejected", "Қайтарылды"

    class Priority(models.TextChoices):
        LOW = "low", "Төмен"
        MEDIUM = "medium", "Орташа"
        HIGH = "high", "Жоғары"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tasks",
    )
    assignee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    deadline = models.DateTimeField(null=True, blank=True)
    progress = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    approval_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "priority"], name="task_status_priority_idx"),
            models.Index(fields=["assignee", "status"], name="task_assignee_status_idx"),
            models.Index(fields=["deadline", "status"], name="task_deadline_status_idx"),
        ]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return bool(
            self.deadline
            and self.deadline < timezone.now()
            and self.status not in (self.Status.DONE, self.Status.APPROVED)
        )


class TaskActivity(models.Model):
    class Action(models.TextChoices):
        CREATED = "created", "Жасалды"
        UPDATED = "updated", "Жаңартылды"
        STATUS_CHANGED = "status_changed", "Статус өзгерді"
        PROGRESS_CHANGED = "progress_changed", "Прогресс өзгерді"
        COMMENTED = "commented", "Комментарий"
        APPROVED = "approved", "Бекітілді"
        REJECTED = "rejected", "Қайтарылды"

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="activities")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="task_activities",
    )
    action = models.CharField(max_length=32, choices=Action.choices, db_index=True)
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "task activities"

    def __str__(self):
        return f"{self.task_id}: {self.action}"


class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="task_comments",
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.task_id}: {self.author}"


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="task_attachments",
    )
    file = models.FileField(upload_to="task_attachments/%Y/%m/")
    original_name = models.CharField(max_length=255)
    size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.task_id}: {self.original_name}"
