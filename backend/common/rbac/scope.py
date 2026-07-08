"""Data-scope helpers — filter querysets by role permissions."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from django.db.models import Q, QuerySet

from .checker import PermissionChecker
from .codes import Perm

if TYPE_CHECKING:
    from apps.accounts.models import User


class DataScope(str, Enum):
    ALL = "all"
    DEPARTMENT = "department"
    OWN = "own"
    NONE = "none"


def get_user_scope(user: User, resource: str) -> DataScope:
    checker = PermissionChecker(user)
    scope_map = {
        "employees": (
            (Perm.EMPLOYEES_VIEW_ALL, DataScope.ALL),
            (Perm.EMPLOYEES_VIEW_DEPARTMENT, DataScope.DEPARTMENT),
        ),
        "departments": (
            (Perm.DEPARTMENTS_VIEW_ALL, DataScope.ALL),
            (Perm.DEPARTMENTS_VIEW_OWN, DataScope.DEPARTMENT),
        ),
        "positions": (
            (Perm.POSITIONS_VIEW_ALL, DataScope.ALL),
            (Perm.POSITIONS_VIEW_OWN, DataScope.DEPARTMENT),
        ),
        "tasks": (
            (Perm.TASKS_VIEW_ALL, DataScope.ALL),
            (Perm.TASKS_VIEW_DEPARTMENT, DataScope.DEPARTMENT),
            (Perm.TASKS_VIEW_OWN, DataScope.OWN),
        ),
        "finance": (
            (Perm.FINANCE_VIEW_ALL, DataScope.ALL),
            (Perm.FINANCE_VIEW_DEPARTMENT, DataScope.DEPARTMENT),
        ),
        "warehouse_movements": (
            (Perm.WAREHOUSE_VIEW_ALL, DataScope.ALL),
            (Perm.WAREHOUSE_VIEW_DEPARTMENT, DataScope.DEPARTMENT),
        ),
    }
    for perm, scope in scope_map.get(resource, ()):
        if checker.has(perm):
            return scope
    return DataScope.NONE


def _department_id(user: User) -> int | None:
    return PermissionChecker(user).department_id()


def scope_queryset(qs: QuerySet, user: User, resource: str) -> QuerySet:
    scope = get_user_scope(user, resource)
    dept_id = _department_id(user)

    if scope == DataScope.ALL:
        return qs

    if scope == DataScope.DEPARTMENT:
        if not dept_id:
            return qs.none()
        if resource == "employees":
            return qs.filter(department_id=dept_id)
        if resource == "departments":
            return qs.filter(id=dept_id)
        if resource == "positions":
            return qs.filter(department_id=dept_id)
        if resource == "tasks":
            return qs.filter(assignee__department_id=dept_id)
        if resource == "finance":
            return qs.filter(created_by__employee_profile__department_id=dept_id)
        if resource == "warehouse_movements":
            return qs.filter(created_by__employee_profile__department_id=dept_id)

    if scope == DataScope.OWN:
        if resource == "tasks":
            return qs.filter(assignee__user=user)

    return qs.none()


def employee_in_scope(user: User, employee) -> bool:
    scope = get_user_scope(user, "employees")
    if scope == DataScope.ALL:
        return True
    if scope == DataScope.DEPARTMENT:
        dept_id = _department_id(user)
        return bool(dept_id and employee.department_id == dept_id)
    return False


def task_in_scope(user: User, task) -> bool:
    scope = get_user_scope(user, "tasks")
    if scope == DataScope.ALL:
        return True
    if scope == DataScope.DEPARTMENT:
        dept_id = _department_id(user)
        return bool(
            dept_id
            and task.assignee
            and task.assignee.department_id == dept_id
        )
    if scope == DataScope.OWN:
        return bool(
            task.assignee
            and task.assignee.user_id == user.id
        )
    return False


def assignee_allowed(user: User, assignee) -> bool:
    """Check whether user may assign a task to the given employee."""
    checker = PermissionChecker(user)
    if checker.has(Perm.TASKS_VIEW_ALL):
        return True
    if checker.has(Perm.TASKS_ASSIGN):
        dept_id = checker.department_id()
        return bool(dept_id and assignee and assignee.department_id == dept_id)
    return False
