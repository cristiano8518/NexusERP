import type { User } from "./api";

const KEYS = {
  access: "access_token",
  refresh: "refresh_token",
  user: "user",
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

export function setAuth(access: string, refresh: string, user: User) {
  localStorage.setItem(KEYS.access, access);
  localStorage.setItem(KEYS.refresh, refresh);
  localStorage.setItem(KEYS.user, JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem(KEYS.access);
  localStorage.removeItem(KEYS.refresh);
  localStorage.removeItem(KEYS.user);
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

export const ROLE_LABELS: Record<User["role"], string> = {
  admin: "Админ",
  manager: "Менеджер",
  employee: "Қызметкер",
};
