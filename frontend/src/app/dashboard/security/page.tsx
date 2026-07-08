"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AuditLog, SecurityLog } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { t } from "@/lib/i18n";

const EVENT_LABELS: Record<string, string> = {
  login_success: "Кіру сәтті",
  login_failed: "Кіру қате",
  logout: "Шығу",
  token_refresh: "Token жаңарту",
  register: "Тіркелу",
};

const AUDIT_LABELS: Record<string, string> = {
  create: "Жасалды",
  update: "Жаңартылды",
  delete: "Жойылды",
  transfer: "Ауыстырылды",
  promote: "Көтерілді",
  demote: "Түсірілді",
  block: "Блокталды",
  unblock: "Блоктан шығарылды",
  upload: "Жүктелді",
};

export default function SecurityPage() {
  const [tab, setTab] = useState<"security" | "audit">("security");
  const [logs, setLogs] = useState<SecurityLog[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.get<{ results: SecurityLog[] }>("/auth/security-logs/"),
      api.get<{ results: AuditLog[] }>("/auth/audit-logs/"),
    ])
      .then(([sec, audit]) => {
        setLogs(sec.data.results ?? []);
        setAuditLogs(audit.data.results ?? []);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader title="Қауіпсіздік" description="Авторизация және бизнес аудиті" />
      <div className="mb-4 flex gap-2">
        <button
          onClick={() => setTab("security")}
          className={`rounded-lg px-4 py-2 text-sm ${tab === "security" ? "bg-brand-600" : "bg-white/5"}`}
        >
          {t.securityLogs}
        </button>
        <button
          onClick={() => setTab("audit")}
          className={`rounded-lg px-4 py-2 text-sm ${tab === "audit" ? "bg-brand-600" : "bg-white/5"}`}
        >
          {t.auditLogs}
        </button>
      </div>

      {loading ? (
        <p className="text-gray-400">{t.loading}</p>
      ) : tab === "security" ? (
        <LogTable
          headers={["Уақыт", "Оқиға", "Пайдаланушы", "IP"]}
          rows={logs.map((log) => [
            new Date(log.created_at).toLocaleString("kk-KZ"),
            EVENT_LABELS[log.event_type] ?? log.event_type,
            log.username || "—",
            log.ip_address || "—",
          ])}
        />
      ) : (
        <LogTable
          headers={["Уақыт", "Әрекет", "Ресурс", "Хабарлама", "Пайдаланушы"]}
          rows={auditLogs.map((log) => [
            new Date(log.created_at).toLocaleString("kk-KZ"),
            AUDIT_LABELS[log.action] ?? log.action,
            `${log.resource_type}:${log.resource_id}`,
            log.message || "—",
            log.actor_name || "—",
          ])}
        />
      )}
    </div>
  );
}

function LogTable({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <div className="glass-card overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-surface-border text-gray-400">
          <tr>{headers.map((h) => <th key={h} className="px-4 py-3">{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-surface-border/50">
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-3 text-xs">{j === 1 ? <Badge label={cell} variant="assigned" /> : cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && <p className="p-4 text-center text-gray-400">Логтар жоқ.</p>}
    </div>
  );
}
