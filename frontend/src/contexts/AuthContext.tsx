"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { api, type User } from "@/lib/api";
import { clearAuth, getStoredPermissions, getStoredUser, setAuth } from "@/lib/auth";

type AuthScope = {
  role: User["role"];
  department_id: number | null;
};

type AuthContextValue = {
  user: User | null;
  permissions: string[];
  scope: AuthScope | null;
  loading: boolean;
  login: (access: string, refresh: string, user: User, permissions?: string[]) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [scope, setScope] = useState<AuthScope | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refreshUser = useCallback(async () => {
    const { data } = await api.get<{
      success: boolean;
      user: User;
      permissions: string[];
      scope: AuthScope;
    }>("/auth/me/");
    setUser(data.user);
    setPermissions(data.permissions ?? []);
    setScope(data.scope ?? null);
    localStorage.setItem("user", JSON.stringify(data.user));
    localStorage.setItem("permissions", JSON.stringify(data.permissions ?? []));
    if (data.scope) {
      localStorage.setItem("scope", JSON.stringify(data.scope));
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    const stored = getStoredUser();
    const storedPerms = getStoredPermissions();
    if (stored) setUser(stored);
    if (storedPerms.length) setPermissions(storedPerms);

    refreshUser()
      .catch(() => {
        clearAuth();
        setUser(null);
        setPermissions([]);
        setScope(null);
      })
      .finally(() => setLoading(false));
  }, [refreshUser]);

  const login = useCallback(
    (access: string, refresh: string, u: User, perms: string[] = []) => {
      setAuth(access, refresh, u, perms);
      setUser(u);
      setPermissions(perms);
    },
    []
  );

  const logout = useCallback(() => {
    clearAuth();
    setUser(null);
    setPermissions([]);
    setScope(null);
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider
      value={{ user, permissions, scope, loading, login, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
