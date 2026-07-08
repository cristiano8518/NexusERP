"use client";

import type { ReactNode } from "react";
import { usePermission } from "@/hooks/usePermission";
import type { PermissionCode } from "@/lib/permissions";

type Props = {
  permission?: PermissionCode;
  anyOf?: PermissionCode[];
  fallback?: ReactNode;
  children: ReactNode;
};

export function PermissionGate({ permission, anyOf, fallback = null, children }: Props) {
  const { can, canAny } = usePermission();

  if (permission && !can(permission)) return <>{fallback}</>;
  if (anyOf && !canAny(...anyOf)) return <>{fallback}</>;

  return <>{children}</>;
}
