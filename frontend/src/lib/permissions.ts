/** RBAC permission codenames — mirrors backend common.rbac.codes.Perm */

export const Perm = {
  EMPLOYEES_VIEW_ALL: "employees.view_all",
  EMPLOYEES_VIEW_DEPARTMENT: "employees.view_department",
  EMPLOYEES_CREATE: "employees.create",
  EMPLOYEES_UPDATE: "employees.update",
  EMPLOYEES_DELETE: "employees.delete",
  EMPLOYEES_BLOCK: "employees.block",
  EMPLOYEES_PROMOTE_MANAGER: "employees.promote_manager",
  EMPLOYEES_DEMOTE_MANAGER: "employees.demote_manager",
  EMPLOYEES_TRANSFER: "employees.transfer",

  DEPARTMENTS_VIEW_ALL: "departments.view_all",
  DEPARTMENTS_VIEW_OWN: "departments.view_own",
  DEPARTMENTS_CREATE: "departments.create",
  DEPARTMENTS_UPDATE: "departments.update",
  DEPARTMENTS_DELETE: "departments.delete",
  DEPARTMENTS_ASSIGN_MANAGER: "departments.assign_manager",

  POSITIONS_VIEW_ALL: "positions.view_all",
  POSITIONS_VIEW_OWN: "positions.view_own",
  POSITIONS_CREATE: "positions.create",
  POSITIONS_UPDATE: "positions.update",
  POSITIONS_DELETE: "positions.delete",

  TASKS_VIEW_ALL: "tasks.view_all",
  TASKS_VIEW_DEPARTMENT: "tasks.view_department",
  TASKS_VIEW_OWN: "tasks.view_own",
  TASKS_CREATE: "tasks.create",
  TASKS_UPDATE: "tasks.update",
  TASKS_DELETE: "tasks.delete",
  TASKS_ASSIGN: "tasks.assign",
  TASKS_APPROVE: "tasks.approve",
  TASKS_COMMENT: "tasks.comment",
  TASKS_UPDATE_OWN_PROGRESS: "tasks.update_own_progress",
  TASKS_ATTACH: "tasks.attach",

  FINANCE_VIEW_ALL: "finance.view_all",
  FINANCE_VIEW_DEPARTMENT: "finance.view_department",
  FINANCE_CREATE: "finance.create",
  FINANCE_UPDATE: "finance.update",
  FINANCE_DELETE: "finance.delete",

  WAREHOUSE_VIEW_ALL: "warehouse.view_all",
  WAREHOUSE_VIEW_DEPARTMENT: "warehouse.view_department",
  WAREHOUSE_MANAGE: "warehouse.manage",

  ANALYTICS_VIEW_COMPANY: "analytics.view_company",
  ANALYTICS_VIEW_DEPARTMENT: "analytics.view_department",
  ANALYTICS_VIEW_PERFORMANCE: "analytics.view_performance",

  REPORTS_VIEW_ALL: "reports.view_all",
  REPORTS_VIEW_DEPARTMENT: "reports.view_department",
  REPORTS_EXPORT: "reports.export",

  SECURITY_VIEW_LOGS: "security.view_logs",
  SYSTEM_MANAGE: "system.manage",

  AI_CHAT: "ai.chat",
  NOTIFICATIONS_VIEW_OWN: "notifications.view_own",
  NOTIFICATIONS_BULK_EMAIL: "notifications.bulk_email",
} as const;

export type PermissionCode = (typeof Perm)[keyof typeof Perm];

/** Route → required permissions (any match grants access). */
export const ROUTE_PERMISSIONS: Record<string, PermissionCode[]> = {
  "/dashboard": [Perm.TASKS_VIEW_ALL, Perm.TASKS_VIEW_DEPARTMENT, Perm.TASKS_VIEW_OWN],
  "/dashboard/profile": [Perm.TASKS_VIEW_OWN, Perm.TASKS_VIEW_DEPARTMENT, Perm.TASKS_VIEW_ALL],
  "/dashboard/tasks": [Perm.TASKS_VIEW_ALL, Perm.TASKS_VIEW_DEPARTMENT, Perm.TASKS_VIEW_OWN],
  "/dashboard/ai": [Perm.AI_CHAT],
  "/dashboard/employees": [Perm.EMPLOYEES_VIEW_ALL, Perm.EMPLOYEES_VIEW_DEPARTMENT],
  "/dashboard/employees/structure": [Perm.DEPARTMENTS_VIEW_ALL, Perm.DEPARTMENTS_VIEW_OWN],
  "/dashboard/warehouse": [Perm.WAREHOUSE_VIEW_ALL, Perm.WAREHOUSE_VIEW_DEPARTMENT],
  "/dashboard/finance": [Perm.FINANCE_VIEW_ALL, Perm.FINANCE_VIEW_DEPARTMENT],
  "/dashboard/analytics": [
    Perm.ANALYTICS_VIEW_COMPANY,
    Perm.ANALYTICS_VIEW_DEPARTMENT,
  ],
  "/dashboard/security": [Perm.SECURITY_VIEW_LOGS],
};

export function canAccessRoute(pathname: string, permissions: string[]): boolean {
  const normalized = pathname.replace(/\/$/, "") || "/dashboard";
  const exact = ROUTE_PERMISSIONS[normalized];
  if (exact) return exact.some((p) => permissions.includes(p));

  if (normalized.startsWith("/dashboard/employees/")) {
    return permissions.some(
      (p) => p === Perm.EMPLOYEES_VIEW_ALL || p === Perm.EMPLOYEES_VIEW_DEPARTMENT
    );
  }
  if (normalized.startsWith("/dashboard/tasks/")) {
    return permissions.some(
      (p) =>
        p === Perm.TASKS_VIEW_ALL ||
        p === Perm.TASKS_VIEW_DEPARTMENT ||
        p === Perm.TASKS_VIEW_OWN
    );
  }
  if (normalized.startsWith("/dashboard/warehouse/")) {
    return permissions.some(
      (p) => p === Perm.WAREHOUSE_VIEW_ALL || p === Perm.WAREHOUSE_VIEW_DEPARTMENT
    );
  }
  return true;
}

export function hasPermission(permissions: string[], code: PermissionCode): boolean {
  return permissions.includes(code);
}

export function hasAnyPermission(permissions: string[], ...codes: PermissionCode[]): boolean {
  return codes.some((c) => permissions.includes(c));
}
