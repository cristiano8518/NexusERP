from django.utils import timezone
from rest_framework import status as drf_status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsEmployeeOrAbove, IsManagerOrAdmin
from apps.notifications.models import Notification
from apps.notifications.services import create_notification

from .models import Task, TaskActivity, TaskComment
from .serializers import TaskCommentSerializer, TaskDetailSerializer, TaskSerializer


WORKFLOW_RULES = {
    Task.Status.ASSIGNED: {Task.Status.IN_PROGRESS},
    Task.Status.IN_PROGRESS: {Task.Status.DONE},
    Task.Status.DONE: {Task.Status.APPROVED, Task.Status.REJECTED},
    Task.Status.REJECTED: {Task.Status.IN_PROGRESS},
}


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsEmployeeOrAbove]
    search_fields = ["title", "description"]
    ordering_fields = ["deadline", "created_at", "status", "priority"]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Task.objects.select_related("created_by", "assignee", "assignee__user")
            .prefetch_related("comments", "activities")
        )
        if user.role == "admin":
            return qs
        if user.role == "manager":
            return qs
        if hasattr(user, "employee_profile"):
            return qs.filter(assignee__user=user)
        return qs.none()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TaskDetailSerializer
        return TaskSerializer

    def get_permissions(self):
        if self.action in ("create", "destroy"):
            return [IsManagerOrAdmin()]
        if self.action in ("update", "partial_update"):
            return [IsEmployeeOrAbove()]
        return super().get_permissions()

    def perform_create(self, serializer):
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
                    f"Deadline: {task.deadline or 'көрсетілмеген'}"
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
                        f"Приоритет: {task.get_priority_display()}\n"
                    ),
                    recipient_list=[assignee.user.email],
                )
            except Exception:
                pass

    def partial_update(self, request, *args, **kwargs):
        task = self.get_object()
        old_status = task.status
        old_progress = task.progress
        old_snapshot = self._task_snapshot(task)
        if "status" in request.data:
            return Response(
                {"detail": "Статусты өзгерту үшін /transition/ endpoint қолданыңыз."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )
        if request.user.role == "employee":
            allowed = {"progress"}
            data = {k: v for k, v in request.data.items() if k in allowed}
            serializer = self.get_serializer(
                task, data=data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            updated_task = serializer.save()
            self._record_update_activity(updated_task, old_status, old_progress, old_snapshot)
            return Response(serializer.data)
        response = super().partial_update(request, *args, **kwargs)
        task.refresh_from_db()
        self._record_update_activity(task, old_status, old_progress, old_snapshot)
        return response

    def update(self, request, *args, **kwargs):
        if request.user.role == "employee":
            return Response(
                {"detail": "Қызметкер тек прогресті және workflow әрекеттерін өзгерте алады."},
                status=drf_status.HTTP_403_FORBIDDEN,
            )
        if "status" in request.data:
            return Response(
                {"detail": "Статусты өзгерту үшін /transition/ endpoint қолданыңыз."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )
        task = self.get_object()
        old_status = task.status
        old_progress = task.progress
        old_snapshot = self._task_snapshot(task)
        response = super().update(request, *args, **kwargs)
        task.refresh_from_db()
        self._record_update_activity(task, old_status, old_progress, old_snapshot)
        return response

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        title = task.title
        self.perform_destroy(task)
        return Response(
            {"success": True, "detail": f"Тапсырма өшірілді: {title}"},
            status=drf_status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        task = self.get_object()
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
            return Response(
                {"detail": "Бұл әрекетке рұқсатыңыз жоқ."},
                status=drf_status.HTTP_403_FORBIDDEN,
            )

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

        action = TaskActivity.Action.STATUS_CHANGED
        if target == Task.Status.APPROVED:
            action = TaskActivity.Action.APPROVED
        elif target == Task.Status.REJECTED:
            action = TaskActivity.Action.REJECTED

        TaskActivity.objects.create(
            task=task,
            actor=request.user,
            action=action,
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

    def _can_change_status(self, user, task, target):
        if user.role in ("admin", "manager"):
            return target in (Task.Status.APPROVED, Task.Status.REJECTED)
        if user.role == "employee":
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
                message=note or "Жұмыс manager тарапынан бекітілді.",
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
