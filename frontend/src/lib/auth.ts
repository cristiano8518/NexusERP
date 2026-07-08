import type { User } from "./api";

const KEYS = {
  access: "access_token",
  refresh: "refresh_token",
  user: "user",
  permissions: "permissions",
  scope: "scope",
} as const;

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(KEYS.access);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(KEYS.user);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function getStoredPermissions(): string[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(KEYS.permissions);
  if (!raw) return [];
  try {
    return JSON.parse(raw) as string[];
  } catch {
    return [];
  }
}

export function setAuth(access: string, refresh: string, user: User, permissions: string[] = []) {
  localStorage.setItem(KEYS.access, access);
  localStorage.setItem(KEYS.refresh, refresh);
  localStorage.setItem(KEYS.user, JSON.stringify(user));
  localStorage.setItem(KEYS.permissions, JSON.stringify(permissions));
}

export function clearAuth() {
  localStorage.removeItem(KEYS.access);
  localStorage.removeItem(KEYS.refresh);
  localStorage.removeItem(KEYS.user);
  localStorage.removeItem(KEYS.permissions);
  localStorage.removeItem(KEYS.scope);
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

export const ROLE_LABELS: Record<User["role"], string> = {
  admin: "Директор",
  manager: "Менеджер",
  employee: "Қызметкер",
};
