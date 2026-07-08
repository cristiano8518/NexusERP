"""
Legacy permission classes — delegate to RBAC where possible.
Prefer common.rbac.Perm + HasPermission for new code.
"""

from rest_framework.permissions import BasePermission

from common.rbac import Perm
from common.rbac.checker import PermissionChecker


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return PermissionChecker(request.user).has(Perm.SYSTEM_MANAGE)


class IsManagerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        checker = PermissionChecker(request.user)
        return checker.has_any(
            Perm.SYSTEM_MANAGE,
            Perm.ANALYTICS_VIEW_DEPARTMENT,
            Perm.EMPLOYEES_VIEW_DEPARTMENT,
        )


class IsEmployeeOrAbove(BasePermission):
    def has_permission(self, request, view):
        checker = PermissionChecker(request.user)
        return checker.has_any(
            Perm.TASKS_VIEW_ALL,
            Perm.TASKS_VIEW_DEPARTMENT,
            Perm.TASKS_VIEW_OWN,
        )
