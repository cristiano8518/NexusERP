"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import clsx from "clsx";
import type { PermissionCode } from "@/lib/permissions";

type NavItem = {
  href: string;
  label: string;
  icon: React.ElementType;
  permissions: PermissionCode[];
};

type Props = {
  items: NavItem[];
  permissions: string[];
};

export function MobileNav({ items, permissions }: Props) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const visible = items.filter((item) =>
    item.permissions.some((p) => permissions.includes(p))
  );

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  return (
    <div className="mb-4 md:hidden">
      <button
        onClick={() => setOpen(!open)}
        className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm"
      >
        {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        Мәзір
      </button>
      {open && (
        <nav className="mt-3 grid gap-1 rounded-2xl border border-white/10 bg-white/5 p-2">
          {visible.map(({ href, label, icon: Icon }) => {
            const active =
              href === "/dashboard"
                ? pathname === href
                : pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "flex items-center gap-3 rounded-xl px-3 py-3 text-sm",
                  active ? "bg-brand-500/20 text-white" : "text-gray-400"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </nav>
      )}
    </div>
  );
}
