from rest_framework.permissions import BasePermission

from .checker import PermissionChecker


class HasPermission(BasePermission):
    """Require a single permission codename on the view."""

    def __init__(self, permission: str):
        self.permission = permission

    def has_permission(self, request, view):
        return PermissionChecker(request.user).has(self.permission)


class HasAnyPermission(BasePermission):
    """Require at least one of the listed permissions."""

    def __init__(self, *permissions: str):
        self.permissions = permissions

    def has_permission(self, request, view):
        checker = PermissionChecker(request.user)
        return checker.has_any(*self.permissions)


def require_any_permission(*permissions: str):
    """Factory for DRF permission_classes — user needs at least one permission."""

    class _Permission(BasePermission):
        def has_permission(self, request, view):
            return PermissionChecker(request.user).has_any(*permissions)

    return _Permission


def require_permission(permission: str):
    """Factory for DRF permission_classes lists."""

    class _Permission(BasePermission):
        def has_permission(self, request, view):
            return PermissionChecker(request.user).has(permission)

    return _Permission
