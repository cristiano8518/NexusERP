"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { canAccessRoute } from "@/lib/permissions";
import { t } from "@/lib/i18n";

export function RoutePermissionGuard({ children }: { children: React.ReactNode }) {
  const { permissions, loading, user } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    if (loading || !user) return;
    if (!canAccessRoute(pathname, permissions)) {
      router.replace("/dashboard?denied=1");
    }
  }, [loading, user, pathname, permissions, router]);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-gray-400">
        {t.loading}
      </div>
    );
  }

  if (user && !canAccessRoute(pathname, permissions)) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-2 text-center">
        <p className="text-lg font-medium text-red-300">{t.accessDenied}</p>
        <p className="text-sm text-gray-400">{t.accessDeniedHint}</p>
      </div>
    );
  }

  if (searchParams.get("denied") === "1" && pathname === "/dashboard") {
    return (
      <>
        <p className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          {t.deniedBanner}
        </p>
        {children}
      </>
    );
  }

  return <>{children}</>;
}
