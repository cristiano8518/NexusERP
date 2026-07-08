"""Permission codenames — extend by adding new constants and registry entries."""


class Perm:
    """Central permission registry. Format: module.action[_scope]."""

    # --- Employees / HR ---
    EMPLOYEES_VIEW_ALL = "employees.view_all"
    EMPLOYEES_VIEW_DEPARTMENT = "employees.view_department"
    EMPLOYEES_CREATE = "employees.create"
    EMPLOYEES_UPDATE = "employees.update"
    EMPLOYEES_DELETE = "employees.delete"
    EMPLOYEES_BLOCK = "employees.block"
    EMPLOYEES_PROMOTE_MANAGER = "employees.promote_manager"
    EMPLOYEES_DEMOTE_MANAGER = "employees.demote_manager"
    EMPLOYEES_TRANSFER = "employees.transfer"

    # --- Departments ---
    DEPARTMENTS_VIEW_ALL = "departments.view_all"
    DEPARTMENTS_VIEW_OWN = "departments.view_own"
    DEPARTMENTS_CREATE = "departments.create"
    DEPARTMENTS_UPDATE = "departments.update"
    DEPARTMENTS_DELETE = "departments.delete"
    DEPARTMENTS_ASSIGN_MANAGER = "departments.assign_manager"

    # --- Positions ---
    POSITIONS_VIEW_ALL = "positions.view_all"
    POSITIONS_VIEW_OWN = "positions.view_own"
    POSITIONS_CREATE = "positions.create"
    POSITIONS_UPDATE = "positions.update"
    POSITIONS_DELETE = "positions.delete"

    # --- Tasks ---
    TASKS_VIEW_ALL = "tasks.view_all"
    TASKS_VIEW_DEPARTMENT = "tasks.view_department"
    TASKS_VIEW_OWN = "tasks.view_own"
    TASKS_CREATE = "tasks.create"
    TASKS_UPDATE = "tasks.update"
    TASKS_DELETE = "tasks.delete"
    TASKS_ASSIGN = "tasks.assign"
    TASKS_APPROVE = "tasks.approve"
    TASKS_COMMENT = "tasks.comment"
    TASKS_UPDATE_OWN_PROGRESS = "tasks.update_own_progress"
    TASKS_ATTACH = "tasks.attach"

    # --- Finance ---
    FINANCE_VIEW_ALL = "finance.view_all"
    FINANCE_VIEW_DEPARTMENT = "finance.view_department"
    FINANCE_CREATE = "finance.create"
    FINANCE_UPDATE = "finance.update"
    FINANCE_DELETE = "finance.delete"

    # --- Warehouse ---
    WAREHOUSE_VIEW_ALL = "warehouse.view_all"
    WAREHOUSE_VIEW_DEPARTMENT = "warehouse.view_department"
    WAREHOUSE_MANAGE = "warehouse.manage"

    # --- Analytics ---
    ANALYTICS_VIEW_COMPANY = "analytics.view_company"
    ANALYTICS_VIEW_DEPARTMENT = "analytics.view_department"
    ANALYTICS_VIEW_PERFORMANCE = "analytics.view_performance"

    # --- Reports ---
    REPORTS_VIEW_ALL = "reports.view_all"
    REPORTS_VIEW_DEPARTMENT = "reports.view_department"
    REPORTS_EXPORT = "reports.export"

    # --- Security / System ---
    SECURITY_VIEW_LOGS = "security.view_logs"
    SYSTEM_MANAGE = "system.manage"

    # --- AI ---
    AI_CHAT = "ai.chat"

    # --- Notifications ---
    NOTIFICATIONS_VIEW_OWN = "notifications.view_own"
    NOTIFICATIONS_BULK_EMAIL = "notifications.bulk_email"
