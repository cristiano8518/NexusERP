"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Bot,
  Boxes,
  CheckSquare,
  LayoutDashboard,
  LogOut,
  Shield,
  UserCircle,
  Users,
  Wallet,
} from "lucide-react";
import clsx from "clsx";
import { AuthGuard } from "@/components/AuthGuard";
import { NotificationBell } from "@/components/notifications/NotificationBell";
import { Badge } from "@/components/ui/Badge";
import { useAuth } from "@/contexts/AuthContext";
import { ROLE_LABELS } from "@/lib/auth";
import type { User } from "@/lib/api";

type NavItem = {
  href: string;
  label: string;
  icon: React.ElementType;
  roles: User["role"][];
};

const nav: NavItem[] = [
  { href: "/dashboard", label: "Басты бет", icon: LayoutDashboard, roles: ["admin", "manager", "employee"] },
  { href: "/dashboard/profile", label: "Профиль", icon: UserCircle, roles: ["admin", "manager", "employee"] },
  { href: "/dashboard/tasks", label: "Тапсырмалар", icon: CheckSquare, roles: ["admin", "manager", "employee"] },
  { href: "/dashboard/ai", label: "AI көмекші", icon: Bot, roles: ["admin", "manager", "employee"] },
  { href: "/dashboard/employees", label: "Қызметкерлер", icon: Users, roles: ["admin", "manager"] },
  { href: "/dashboard/warehouse", label: "Қойма", icon: Boxes, roles: ["admin", "manager"] },
  { href: "/dashboard/finance", label: "Қаржы", icon: Wallet, roles: ["admin", "manager"] },
  { href: "/dashboard/analytics", label: "Аналитика & Есептер", icon: BarChart3, roles: ["admin", "manager"] },
  { href: "/dashboard/security", label: "Қауіпсіздік", icon: Shield, roles: ["admin"] },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const visibleNav = nav.filter((item) => user && item.roles.includes(user.role));

  return (
    <AuthGuard>
      <div className="animated-shell flex min-h-screen">
        <aside className="m-4 hidden w-72 flex-col rounded-[2rem] border border-white/10 bg-white/[0.07] p-4 shadow-2xl shadow-black/30 backdrop-blur-2xl md:flex">
          <div className="mb-8 flex items-center gap-3 px-2 pt-2">
            <div className="orbital-ring flex h-11 w-11 items-center justify-center rounded-2xl text-sm font-bold shadow-lg shadow-brand-900/30">
              N
            </div>
            <div>
              <span className="font-semibold text-white">NexusERP</span>
              <p className="text-xs text-gray-500">Бизнес жүйесі</p>
            </div>
          </div>
          <nav className="flex flex-1 flex-col gap-1">
            {visibleNav.map(({ href, label, icon: Icon }) => {
              const active = href === "/dashboard" ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);
              return (
                <Link
                  key={href}
                  href={href}
                  className={clsx(
                    "group flex items-center gap-3 rounded-2xl px-3 py-3 text-sm transition duration-300",
                    active
                      ? "bg-gradient-to-r from-brand-500/25 to-cyan-500/10 text-white shadow-lg shadow-brand-950/20"
                      : "text-gray-400 hover:bg-white/[0.07] hover:text-white"
                  )}
                >
                  <span className={clsx(
                    "rounded-xl p-2 transition",
                    active
                      ? "bg-white/10 text-cyan-200"
                      : "bg-white/[0.04] text-gray-400 group-hover:text-white"
                  )}>
                    <Icon className="h-4 w-4" />
                  </span>
                  {label}
                </Link>
              );
            })}
          </nav>
        </aside>
        <div className="flex flex-1 flex-col">
          <div className="flex-1 overflow-auto p-4 md:p-6">
            {user && (
              <div className="mb-4 flex items-center justify-end gap-3 text-sm">
                <NotificationBell />
                <Badge label={ROLE_LABELS[user.role]} variant={user.role} />
                <button
                  onClick={logout}
                  className="inline-flex items-center gap-2 rounded-2xl border border-red-400/20 bg-red-500/10 px-3 py-2 text-xs font-medium text-red-200 transition hover:bg-red-500/20"
                >
                  <LogOut className="h-4 w-4" />
                  Шығу
                </button>
              </div>
            )}
            {children}
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
