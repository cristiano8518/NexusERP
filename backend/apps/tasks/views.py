import logging

from django.utils import timezone
from rest_framework import status as drf_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from common.audit import log_audit_event
from common.rbac import Perm
from common.rbac.checker import PermissionChecker
from common.rbac.drf_permissions import require_permission
from common.rbac.scope import assignee_allowed, scope_queryset, task_in_scope

from .models import Task, TaskActivity, TaskAttachment, TaskComment
from .serializers import (
    TaskAttachmentSerializer,
    TaskCommentSerializer,
    TaskDetailSerializer,
    TaskSerializer,
)

logger = logging.getLogger("nexuserp")


WORKFLOW_RULES = {
    Task.Status.ASSIGNED: {Task.Status.IN_PROGRESS},
    Task.Status.IN_PROGRESS: {Task.Status.DONE},
    Task.Status.DONE: {Task.Status.APPROVED, Task.Status.REJECTED},
    Task.Status.REJECTED: {Task.Status.IN_PROGRESS},
}


def _forbidden(message="Недостаточно прав доступа."):
    raise PermissionDenied(message)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["title", "description"]
    ordering_fields = ["deadline", "created_at", "status", "priority"]

    def get_queryset(self):
        qs = Task.objects.select_related(
            "created_by", "assignee", "assignee__user", "assignee__department"
        ).prefetch_related("comments", "activities")
        return scope_queryset(qs, self.request.user, "tasks")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TaskDetailSerializer
        return TaskSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), require_permission(Perm.TASKS_CREATE)()]
        if self.action == "destroy":
            return [IsAuthenticated(), require_permission(Perm.TASKS_DELETE)()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        checker = PermissionChecker(request.user)
        if not checker.has_any(
            Perm.TASKS_VIEW_ALL, Perm.TASKS_VIEW_DEPARTMENT, Perm.TASKS_VIEW_OWN
        ):
            _forbidden()
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        if not task_in_scope(request.user, task):
            _forbidden()
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        assignee = serializer.validated_data.get("assignee")
        if assignee and not assignee_allowed(self.request.user, assignee):
            raise ValidationError(
                {"assignee": "Менеджер тек өз бөліміндегі қызметкерге тапсырма бере алады."}
            )
        task = serializer.save(created_by=self.request.user, status=Task.Status.ASSIGNED)
        TaskActivity.objects.create(
            task=task,
            actor=self.request.user,
            action=TaskActivity.Action.CREATED,
            to_status=task.status,
            message="Тапсырма жасалып, орындаушыға берілді.",
        )
        assignee = task.assignee
        if assignee:
            create_notification(
                recipient=assignee.user,
                actor=self.request.user,
                notification_type=Notification.Type.TASK_ASSIGNED,
                priority=Notification.Priority.HIGH if task.priority == Task.Priority.HIGH else Notification.Priority.NORMAL,
                title=f"Жаңа тапсырма: {task.title}",
                message=(
                    f"{self.request.user.username} сізге жаңа тапсырма берді. "
                    f"Мерзім: {task.deadline or 'көрсетілмеген'}"
                ),
                link=f"/dashboard/tasks/{task.id}",
                metadata={"task_id": task.id},
            )
        if assignee and assignee.user.email:
            try:
                from apps.notifications.tasks import send_email_task

                send_email_task.delay(
                    subject=f"[NexusERP] Жаңа тапсырма: {task.title}",
                    message=(
                        f"Сәлем, {assignee.user.first_name or assignee.user.username}!\n\n"
                        f"Сізге жаңа тапсырма тағайындалды: {task.title}\n"
                        f"Мерзім: {task.deadline or 'көрсетілмеген'}\n"
                        f"Басымдық: {task.get_priority_display()}\n"
                    ),
                    recipient_list=[assignee.user.email],
                )
            except Exception as exc:
                logger.warning(
                    "Task notification email enqueue failed (task_id=%s, assignee_id=%s): %s",
                    task.id,
                    assignee.id,
                    exc,
                )

    def partial_update(self, request, *args, **kwargs):
        task = self.get_object()
        if not task_in_scope(request.user, task):
            _forbidden()

        checker = PermissionChecker(request.user)
        old_status = task.status
        old_progress = task.progress
        old_snapshot = self._task_snapshot(task)

        if "status" in request.data:
            return Response(
                {"detail": "Статусты өзгерту үшін /transition/ endpoint қолданыңыз."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        if checker.has(Perm.TASKS_UPDATE_OWN_PROGRESS) and not checker.has_any(
            Perm.TASKS_UPDATE, Perm.TASKS_ASSIGN
        ):
            allowed = {"progress"}
            data = {k: v for k, v in request.data.items() if k in allowed}
            serializer = self.get_serializer(task, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_task = serializer.save()
            self._record_update_activity(updated_task, old_status, old_progress, old_snapshot)
            return Response(serializer.data)

        if not checker.has_any(Perm.TASKS_UPDATE, Perm.TASKS_ASSIGN):
            _forbidden()

        if "assignee" in request.data:
            serializer = self.get_serializer(task, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            assignee = serializer.validated_data.get("assignee")
            if assignee and not assignee_allowed(request.user, assignee):
                raise ValidationError(
                    {"assignee": "Менеджер тек өз бөліміндегі қызметкерге тапсырма бере алады."}
                )

        response = super().partial_update(request, *args, **kwargs)
        task.refresh_from_db()
        self._record_update_activity(task, old_status, old_progress, old_snapshot)
        return response

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        if not task_in_scope(request.user, task):
            _forbidden()

        checker = PermissionChecker(request.user)
        if checker.has(Perm.TASKS_UPDATE_OWN_PROGRESS) and not checker.has_any(
            Perm.TASKS_UPDATE, Perm.TASKS_ASSIGN
        ):
            return Response(
                {"detail": "Қызметкер тек прогресті өзгерте алады."},
                status=drf_status.HTTP_403_FORBIDDEN,
            )
        if not checker.has_any(Perm.TASKS_UPDATE, Perm.TASKS_ASSIGN):
            _forbidden()

        if "status" in request.data:
            return Response(
                {"detail": "Статусты өзгерту үшін /transition/ endpoint қолданыңыз."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(task, data=request.data)
        serializer.is_valid(raise_exception=True)
        assignee = serializer.validated_data.get("assignee")
        if assignee and not assignee_allowed(request.user, assignee):
            raise ValidationError(
                {"assignee": "Менеджер тек өз бөліміндегі қызметкерге тапсырма бере алады."}
            )

        old_status = task.status
        old_progress = task.progress
        old_snapshot = self._task_snapshot(task)
        response = super().update(request, *args, **kwargs)
        task.refresh_from_db()
        self._record_update_activity(task, old_status, old_progress, old_snapshot)
        return response

    def destroy(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.TASKS_DELETE):
            _forbidden()
        task = self.get_object()
        if not task_in_scope(request.user, task):
            _forbidden()
        title = task.title
        self.perform_destroy(task)
        return Response(
            {"success": True, "detail": f"Тапсырма өшірілді: {title}"},
            status=drf_status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        task = self.get_object()
        if not task_in_scope(request.user, task):
            _forbidden()

        target = request.data.get("status")
        note = (request.data.get("note") or "").strip()

        if target not in dict(Task.Status.choices):
            return Response(
                {"detail": "Белгісіз статус."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        allowed = WORKFLOW_RULES.get(task.status, set())
        if target not in allowed:
            return Response(
                {
                    "detail": (
                        f"{task.get_status_display()} статусынан "
                        f"{dict(Task.Status.choices)[target]} статусына ауысуға болмайды."
                    )
                },
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        if not self._can_change_status(request.user, task, target):
            _forbidden()

        previous = task.status
        now = timezone.now()
        task.status = target
        if target == Task.Status.IN_PROGRESS:
            task.started_at = task.started_at or now
            if task.progress == 0:
                task.progress = 10
        elif target == Task.Status.DONE:
            task.submitted_at = now
            task.completed_at = now
            task.progress = 100
        elif target == Task.Status.APPROVED:
            task.approved_at = now
            task.approval_note = note
            task.progress = 100
        elif target == Task.Status.REJECTED:
            task.rejected_at = now
            task.approval_note = note
            task.progress = min(task.progress, 90)
        task.save()

        action_type = TaskActivity.Action.STATUS_CHANGED
        if target == Task.Status.APPROVED:
            action_type = TaskActivity.Action.APPROVED
        elif target == Task.Status.REJECTED:
            action_type = TaskActivity.Action.REJECTED

        TaskActivity.objects.create(
            task=task,
            actor=request.user,
            action=action_type,
            from_status=previous,
            to_status=target,
            message=note,
        )

        self._send_transition_notification(task, previous, target, note)

        serializer = TaskDetailSerializer(task, context=self.get_serializer_context())
        return Response({"success": True, "task": serializer.data})

    @action(detail=True, methods=["post"], url_path="comments")
    def add_comment(self, request, pk=None):
        task = self.get_object()
        if not task_in_scope(request.user, task):
            _forbidden()
        if not PermissionChecker(request.user).has(Perm.TASKS_COMMENT):
            _forbidden()

        serializer = TaskCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(task=task, author=request.user)
        TaskActivity.objects.create(
            task=task,
            actor=request.user,
            action=TaskActivity.Action.COMMENTED,
            message=comment.message[:500],
        )
        recipients = []
        if task.created_by_id != request.user.id:
            recipients.append(task.created_by)
        if task.assignee and task.assignee.user_id != request.user.id:
            recipients.append(task.assignee.user)
        for recipient in recipients:
            create_notification(
                recipient=recipient,
                actor=request.user,
                notification_type=Notification.Type.TASK_COMMENT,
                title=f"Комментарий: {task.title}",
                message=comment.message[:180],
                link=f"/dashboard/tasks/{task.id}",
                metadata={"task_id": task.id, "comment_id": comment.id},
            )
        return Response(
            {"success": True, "comment": TaskCommentSerializer(comment).data},
            status=drf_status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="attachments",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_attachment(self, request, pk=None):
        task = self.get_object()
        if not task_in_scope(request.user, task):
            _forbidden()
        if not PermissionChecker(request.user).has(Perm.TASKS_ATTACH):
            _forbidden()

        upload = request.FILES.get("file")
        if not upload:
            return Response({"detail": "Файл жоқ."}, status=drf_status.HTTP_400_BAD_REQUEST)
        if upload.size > 10 * 1024 * 1024:
            return Response({"detail": "Файл 10 МБ-тан аспауы керек."}, status=drf_status.HTTP_400_BAD_REQUEST)

        attachment = TaskAttachment.objects.create(
            task=task,
            uploaded_by=request.user,
            file=upload,
            original_name=upload.name,
            size=upload.size,
        )
        TaskActivity.objects.create(
            task=task,
            actor=request.user,
            action=TaskActivity.Action.UPDATED,
            message=f"Файл жүктелді: {upload.name}",
        )
        log_audit_event(
            request=request,
            action="upload",
            resource_type="task_attachment",
            resource_id=attachment.id,
            message=f"{task.title}: {upload.name}",
        )
        serializer = TaskAttachmentSerializer(attachment, context=self.get_serializer_context())
        return Response({"success": True, "attachment": serializer.data}, status=drf_status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"attachments/(?P<attachment_id>\d+)")
    def delete_attachment(self, request, pk=None, attachment_id=None):
        task = self.get_object()
        if not task_in_scope(request.user, task):
            _forbidden()
        checker = PermissionChecker(request.user)
        attachment = TaskAttachment.objects.filter(task=task, id=attachment_id).first()
        if not attachment:
            return Response({"detail": "Файл табылмады."}, status=drf_status.HTTP_404_NOT_FOUND)
        if not checker.has_any(Perm.TASKS_DELETE, Perm.SYSTEM_MANAGE) and attachment.uploaded_by_id != request.user.id:
            _forbidden()
        name = attachment.original_name
        attachment.file.delete(save=False)
        attachment.delete()
        log_audit_event(
            request=request,
            action="delete",
            resource_type="task_attachment",
            resource_id=attachment_id,
            message=f"{task.title}: {name}",
        )
        return Response({"success": True, "detail": "Файл жойылды."})

    def _can_change_status(self, user, task, target):
        checker = PermissionChecker(user)
        if checker.has(Perm.TASKS_APPROVE):
            if checker.has(Perm.TASKS_VIEW_ALL):
                return target in (Task.Status.APPROVED, Task.Status.REJECTED)
            if checker.has(Perm.TASKS_VIEW_DEPARTMENT) and task.assignee:
                return (
                    task.assignee.department_id == checker.department_id()
                    and target in (Task.Status.APPROVED, Task.Status.REJECTED)
                )
        if checker.has(Perm.TASKS_UPDATE_OWN_PROGRESS):
            return (
                task.assignee
                and task.assignee.user_id == user.id
                and target in (Task.Status.IN_PROGRESS, Task.Status.DONE)
            )
        return False

    def _task_snapshot(self, task):
        return {
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "assignee_id": task.assignee_id,
            "deadline": task.deadline,
            "progress": task.progress,
        }

    def _record_update_activity(self, task, old_status, old_progress, old_snapshot=None):
        if task.status != old_status:
            TaskActivity.objects.create(
                task=task,
                actor=self.request.user,
                action=TaskActivity.Action.STATUS_CHANGED,
                from_status=old_status,
                to_status=task.status,
            )
        elif task.progress != old_progress:
            TaskActivity.objects.create(
                task=task,
                actor=self.request.user,
                action=TaskActivity.Action.PROGRESS_CHANGED,
                message=f"{old_progress}% → {task.progress}%",
            )
        elif old_snapshot and self._task_snapshot(task) != old_snapshot:
            TaskActivity.objects.create(
                task=task,
                actor=self.request.user,
                action=TaskActivity.Action.UPDATED,
                message="Тапсырма деректері жаңартылды.",
            )

    def _send_transition_notification(self, task, previous, target, note):
        actor = self.request.user
        link = f"/dashboard/tasks/{task.id}"
        metadata = {"task_id": task.id, "from_status": previous, "to_status": target}

        if target == Task.Status.IN_PROGRESS and task.created_by_id != actor.id:
            create_notification(
                recipient=task.created_by,
                actor=actor,
                notification_type=Notification.Type.TASK_STARTED,
                title=f"Тапсырма басталды: {task.title}",
                message=f"{actor.username} тапсырманы орындауды бастады.",
                link=link,
                metadata=metadata,
            )
        elif target == Task.Status.DONE and task.created_by_id != actor.id:
            create_notification(
                recipient=task.created_by,
                actor=actor,
                notification_type=Notification.Type.TASK_SUBMITTED,
                priority=Notification.Priority.HIGH,
                title=f"Тексеруге жіберілді: {task.title}",
                message=f"{actor.username} тапсырманы аяқтап, approval-ға жіберді.",
                link=link,
                metadata=metadata,
            )
        elif target == Task.Status.APPROVED and task.assignee:
            create_notification(
                recipient=task.assignee.user,
                actor=actor,
                notification_type=Notification.Type.TASK_APPROVED,
                title=f"Тапсырма бекітілді: {task.title}",
                message=note or "Жұмыс менеджер тарапынан бекітілді.",
                link=link,
                metadata=metadata,
            )
        elif target == Task.Status.REJECTED and task.assignee:
            create_notification(
                recipient=task.assignee.user,
                actor=actor,
                notification_type=Notification.Type.TASK_REJECTED,
                priority=Notification.Priority.HIGH,
                title=f"Тапсырма қайтарылды: {task.title}",
                message=note or "Тапсырма қайта өңдеуге жіберілді.",
                link=link,
                metadata=metadata,
            )
