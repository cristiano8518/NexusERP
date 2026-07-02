"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PaginatedResponse, SecurityLog } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";

const EVENT_LABELS: Record<string, string> = {
  login_success: "Кіру сәтті",
  login_failed: "Кіру қате",
  logout: "Шығу",
  token_refresh: "Token жаңарту",
  register: "Тіркелу",
};

export default function SecurityPage() {
  const [logs, setLogs] = useState<SecurityLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<PaginatedResponse<SecurityLog>>("/auth/security-logs/")
      .then((res) => setLogs(res.data.results ?? []))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader
        title="Қауіпсіздік логтары"
        description="Кіру, тіркелу және авторизация оқиғалары (тек Әкімші)"
      />

      {loading ? (
        <p className="text-gray-400">Жүктелуде...</p>
      ) : (
        <div className="glass-card overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-surface-border text-gray-400">
              <tr>
                <th className="px-4 py-3">Уақыт</th>
                <th className="px-4 py-3">Оқиға</th>
                <th className="px-4 py-3">Пайдаланушы</th>
                <th className="px-4 py-3">IP</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b border-surface-border/50">
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {new Date(log.created_at).toLocaleString("kk-KZ")}
                  </td>
                  <td className="px-4 py-3">
                    <Badge
                      label={EVENT_LABELS[log.event_type] ?? log.event_type}
                      variant={log.event_type.includes("failed") ? "rejected" : "approved"}
                    />
                  </td>
                  <td className="px-4 py-3">{log.username || "—"}</td>
                  <td className="px-4 py-3 font-mono text-xs">{log.ip_address || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {logs.length === 0 && (
            <p className="p-4 text-center text-gray-400">Логтар әзірге жоқ.</p>
          )}
        </div>
      )}
    </div>
  );
}
