from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import WILDCARD, all_permission_codes, get_role_permissions

if TYPE_CHECKING:
    from apps.accounts.models import User


class PermissionChecker:
    """Evaluates RBAC permissions for a user."""

    def __init__(self, user: User):
        self.user = user
        self._permissions: frozenset[str] | None = None

    @property
    def permissions(self) -> frozenset[str]:
        if self._permissions is None:
            role_perms = get_role_permissions(getattr(self.user, "role", ""))
            if WILDCARD in role_perms:
                self._permissions = all_permission_codes()
            else:
                self._permissions = role_perms
        return self._permissions

    def has(self, permission: str) -> bool:
        if not self.user or not self.user.is_authenticated:
            return False
        if not self.user.is_active:
            return False
        return permission in self.permissions

    def has_any(self, *permissions: str) -> bool:
        return any(self.has(p) for p in permissions)

    def has_all(self, *permissions: str) -> bool:
        return all(self.has(p) for p in permissions)

    def department_id(self) -> int | None:
        profile = getattr(self.user, "employee_profile", None)
        return profile.department_id if profile else None

    def employee_id(self) -> int | None:
        profile = getattr(self.user, "employee_profile", None)
        return profile.id if profile else None

    def is_director(self) -> bool:
        return getattr(self.user, "role", None) == "admin"

    def is_manager(self) -> bool:
        return getattr(self.user, "role", None) == "manager"

    def is_employee(self) -> bool:
        return getattr(self.user, "role", None) == "employee"


def get_user_permissions(user: User) -> list[str]:
    return sorted(PermissionChecker(user).permissions)
