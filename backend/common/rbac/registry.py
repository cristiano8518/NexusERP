"""
Role → permission mapping.

To add a new role (e.g. deputy_director, team_lead):
1. Add the role code to accounts.models.Role (or a future RoleDefinition table).
2. Register permissions in ROLE_PERMISSIONS below.
3. Optionally set a default DataScope in ROLE_DEFAULT_SCOPES.
"""

from apps.accounts.models import Role

from .codes import Perm

# Wildcard grants every defined permission.
WILDCARD = "*"

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    Role.ADMIN: frozenset({WILDCARD}),
    Role.MANAGER: frozenset({
        Perm.EMPLOYEES_VIEW_DEPARTMENT,
        Perm.DEPARTMENTS_VIEW_OWN,
        Perm.POSITIONS_VIEW_OWN,
        Perm.TASKS_VIEW_DEPARTMENT,
        Perm.TASKS_CREATE,
        Perm.TASKS_UPDATE,
        Perm.TASKS_ASSIGN,
        Perm.TASKS_APPROVE,
        Perm.TASKS_COMMENT,
        Perm.TASKS_ATTACH,
        Perm.FINANCE_VIEW_DEPARTMENT,
        Perm.FINANCE_CREATE,
        Perm.FINANCE_UPDATE,
        Perm.FINANCE_DELETE,
        Perm.WAREHOUSE_VIEW_DEPARTMENT,
        Perm.WAREHOUSE_MANAGE,
        Perm.ANALYTICS_VIEW_DEPARTMENT,
        Perm.REPORTS_VIEW_DEPARTMENT,
        Perm.REPORTS_EXPORT,
        Perm.AI_CHAT,
        Perm.NOTIFICATIONS_VIEW_OWN,
    }),
    Role.EMPLOYEE: frozenset({
        Perm.TASKS_VIEW_OWN,
        Perm.TASKS_UPDATE_OWN_PROGRESS,
        Perm.TASKS_COMMENT,
        Perm.TASKS_ATTACH,
        Perm.AI_CHAT,
        Perm.NOTIFICATIONS_VIEW_OWN,
    }),
}

# Hook for dynamically registered roles (plugins, future DB-backed roles).
EXTRA_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {}


def get_role_permissions(role: str) -> frozenset[str]:
    if role == Role.ADMIN:
        return ROLE_PERMISSIONS[Role.ADMIN]
    base = ROLE_PERMISSIONS.get(role, frozenset())
    extra = EXTRA_ROLE_PERMISSIONS.get(role, frozenset())
    return base | extra


def register_role_permissions(role: str, permissions: frozenset[str]) -> None:
    """Register permissions for a custom role at runtime."""
    EXTRA_ROLE_PERMISSIONS[role] = permissions


def all_permission_codes() -> frozenset[str]:
    codes = set()
    for name in dir(Perm):
        if name.isupper() and not name.startswith("_"):
            codes.add(getattr(Perm, name))
    return frozenset(codes)
