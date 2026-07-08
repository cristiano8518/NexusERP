"use client";

import { useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import type { PermissionCode } from "@/lib/permissions";
import { hasAnyPermission, hasPermission } from "@/lib/permissions";

export function usePermission() {
  const { permissions } = useAuth();

  const can = useCallback(
    (code: PermissionCode) => hasPermission(permissions, code),
    [permissions]
  );

  const canAny = useCallback(
    (...codes: PermissionCode[]) => hasAnyPermission(permissions, ...codes),
    [permissions]
  );

  const isDirector = useCallback(
    () => hasPermission(permissions, "system.manage"),
    [permissions]
  );

  const isManager = useCallback(
    () =>
      hasPermission(permissions, "employees.view_department") &&
      !hasPermission(permissions, "system.manage"),
    [permissions]
  );

  const isEmployee = useCallback(
    () =>
      hasPermission(permissions, "tasks.view_own") &&
      !hasPermission(permissions, "employees.view_department"),
    [permissions]
  );

  return {
    permissions,
    can,
    canAny,
    isDirector,
    isManager,
    isEmployee,
  };
}
