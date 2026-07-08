"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Download, FileSpreadsheet, Printer, TrendingUp } from "lucide-react";
import { api } from "@/lib/api";
import type { MonthlyFinance, PerformanceStats } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { LoadingState } from "@/components/ui/StateBlock";
import { useToast } from "@/contexts/ToastContext";
import { usePermission } from "@/hooks/usePermission";
import { Perm } from "@/lib/permissions";
import { t } from "@/lib/i18n";

type DashboardData = {
  employees: { total: number; managers?: number };
  tasks: { completion_rate: number; active?: number; overdue?: number };
  finance: { income: number; expense: number; balance: number };
  warehouse: { products: number; low_stock: number };
  departments?: { total: number };
};

type ReportSummary = {
  generated_at: string;
  data: {
    employees: { active: number; total: number };
    tasks: { total: number; done: number; approved: number; overdue: number; completion_rate: number };
    finance: { income: number; expense: number; balance: number };
    warehouse: { products: number; low_stock: number; movements: number };
  };
};

const reports = [
  { title: "Тапсырмалардың орындалуы", description: "Статус, прогресс, мерзім.", endpoint: "/reports/tasks.csv", filename: "nexuserp_tasks_report.csv" },
  { title: "Айлық қаржы есебі", description: "Кіріс/шығыс жазбалары.", endpoint: "/reports/finance.csv", filename: "nexuserp_finance_report.csv" },
  { title: "Қойма қоры есебі", description: "Қалдықтар және қойма құны.", endpoint: "/reports/warehouse.csv", filename: "nexuserp_warehouse_report.csv" },
  { title: "Қызметкерлер есебі", description: "Бөлім, лауазым, рөл.", endpoint: "/reports/employees.csv", filename: "nexuserp_employees_report.csv" },
];

function MetricCard({ title, value, hint, tone = "text-white" }: { title: string; value: string | number; hint: string; tone?: string }) {
  return (
    <div className="premium-card p-5">
      <p className="text-sm text-gray-400">{title}</p>
      <p className={`mt-3 text-3xl font-black ${tone}`}>{value}</p>
      <p className="mt-1 text-xs text-gray-500">{hint}</p>
    </div>
  );
}

export default function AnalyticsPage() {
  const toast = useToast();
  const { can } = usePermission();
  const [summary, setSummary] = useState<DashboardData | null>(null);
  const [reportSummary, setReportSummary] = useState<ReportSummary | null>(null);
  const [monthly, setMonthly] = useState<MonthlyFinance[]>([]);
  const [performance, setPerformance] = useState<PerformanceStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    const reqs = [
      api.get("/analytics/dashboard/"),
      api.get("/analytics/monthly-finance/"),
      api.get<ReportSummary>("/reports/summary/"),
      api.get<{ data: PerformanceStats }>("/analytics/performance/").catch(() => ({ data: { data: null } })),
    ];
    Promise.all(reqs)
      .then(([dashboard, monthlyFinance, reportsSummary, perf]) => {
        setSummary(dashboard.data.data);
        setMonthly(monthlyFinance.data.data);
        setReportSummary(reportsSummary.data);
        setPerformance(perf.data.data);
      })
      .catch((err: { response?: { status?: number } }) => {
        setError(`Аналитика API қатесі (${err.response?.status ?? "?"}).`);
      });
  }, []);

  async function downloadReport(endpoint: string, filename: string) {
    if (!can(Perm.REPORTS_EXPORT)) {
      toast.error(t.accessDenied);
      return;
    }
    try {
      const response = await api.get(endpoint, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Есеп жүктелді", filename);
    } catch {
      toast.error("Есеп жүктелмеді");
    }
  }

  if (error) {
    return (
      <div>
        <PageHeader title="Аналитика & Есептер" description="Көрсеткіштер және экспорт" />
        <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">{error}</p>
      </div>
    );
  }

  if (!summary) return <LoadingState label="Аналитика жүктелуде..." />;

  const maxBar = Math.max(...monthly.flatMap((m) => [m.income, m.expense]), 1);

  return (
    <div>
      <PageHeader
        title="Аналитика & Есептер"
        description="Көрсеткіштер, өнімділік және экспорт"
        action={
          <button onClick={() => window.print()} className="ghost-button px-4 py-2 text-sm">
            <Printer className="h-4 w-4" />
            Басып шығару
          </button>
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Тапсырма орындалуы" value={`${summary.tasks.completion_rate}%`} hint="аяқталу %" tone="text-brand-300" />
        <MetricCard title="Белсенді тапсырмалар" value={summary.tasks.active ?? "—"} hint={`мерзімі өткен ${summary.tasks.overdue ?? 0}`} tone="text-amber-200" />
        <MetricCard title="Қызметкерлер" value={summary.employees.total} hint={`менеджер ${summary.employees.managers ?? 0}`} />
        <MetricCard title="Баланс" value={`${summary.finance.balance.toLocaleString()} ₸`} hint="табыс - шығын" tone={summary.finance.balance >= 0 ? "text-emerald-300" : "text-red-300"} />
      </div>

      {performance && (
        <section className="premium-card mb-6 p-6">
          <div className="mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-brand-300" />
            <h3 className="text-xl font-bold">{t.performance}</h3>
          </div>
          <div className="grid gap-6 xl:grid-cols-3">
            <div>
              <h4 className="mb-2 text-sm font-medium text-gray-400">{t.departments}</h4>
              <div className="space-y-2 text-sm">
                {performance.departments.map((d) => (
                  <div key={d.id} className="rounded-xl bg-white/5 p-3">
                    <p className="font-medium">{d.name}</p>
                    <p className="text-xs text-gray-500">{d.employee_count} қызметкер · {d.completion_rate}%</p>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4 className="mb-2 text-sm font-medium text-gray-400">{t.managers}</h4>
              <div className="space-y-2 text-sm">
                {performance.managers.map((m) => (
                  <div key={m.id} className="rounded-xl bg-white/5 p-3">
                    <p className="font-medium">{m.name}</p>
                    <p className="text-xs text-gray-500">{m.department} · команда {m.team_size}</p>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4 className="mb-2 text-sm font-medium text-gray-400">{t.employees}</h4>
              <div className="max-h-64 space-y-2 overflow-auto text-sm">
                {performance.employees.map((e) => (
                  <div key={e.id} className="rounded-xl bg-white/5 p-3">
                    <p className="font-medium">{e.name}</p>
                    <p className="text-xs text-gray-500">{e.active_tasks} белсенді · {e.completion_rate}%</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}

      <section className="premium-card p-6">
        <h3 className="mb-4 text-xl font-bold">Айлар бойынша қаржы</h3>
        <div className="space-y-4">
          {monthly.map((m) => (
            <div key={m.month}>
              <p className="mb-2 text-sm text-gray-300">{m.month}</p>
              <div className="grid gap-2 sm:grid-cols-2">
                <div className="h-2 rounded-full bg-white/5"><div className="h-full rounded-full bg-emerald-500" style={{ width: `${(m.income / maxBar) * 100}%` }} /></div>
                <div className="h-2 rounded-full bg-white/5"><div className="h-full rounded-full bg-red-500" style={{ width: `${(m.expense / maxBar) * 100}%` }} /></div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {can(Perm.REPORTS_EXPORT) && (
        <section className="mt-6">
          <h2 className="mb-4 text-xl font-bold">Экспорт орталығы</h2>
          <div className="grid gap-4 lg:grid-cols-2">
            {reports.map((report) => (
              <div key={report.endpoint} className="premium-card p-5">
                <div className="mb-4 flex gap-3">
                  <FileSpreadsheet className="h-5 w-5 text-brand-300" />
                  <div>
                    <h3 className="font-semibold">{report.title}</h3>
                    <p className="text-sm text-gray-400">{report.description}</p>
                  </div>
                </div>
                <button onClick={() => downloadReport(report.endpoint, report.filename)} className="premium-button px-4 py-2 text-sm">
                  <Download className="h-4 w-4" />
                  CSV жүктеу
                </button>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
