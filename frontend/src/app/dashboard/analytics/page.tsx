"use client";

import { useEffect, useState } from "react";
import { Download, FileSpreadsheet, Printer } from "lucide-react";
import { api } from "@/lib/api";
import type { MonthlyFinance } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { LoadingState } from "@/components/ui/StateBlock";
import { useToast } from "@/contexts/ToastContext";

type DashboardData = {
  tasks: { completion_rate: number };
  finance: { income: number; expense: number; balance: number };
  warehouse: { products: number; low_stock: number };
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
  {
    title: "Тапсырмалардың орындалуы",
    description: "Тапсырмалар, статус, прогресс, мерзім және кешіккен жұмыстар.",
    endpoint: "/reports/tasks.csv",
    filename: "nexuserp_tasks_report.csv",
  },
  {
    title: "Айлық қаржы есебі",
    description: "Кіріс/шығыс жазбалары, категория, сома және дата.",
    endpoint: "/reports/finance.csv",
    filename: "nexuserp_finance_report.csv",
  },
  {
    title: "Қойма қоры есебі",
    description: "Қалдықтар, қойма құны және төмен қор көрсеткіштері.",
    endpoint: "/reports/warehouse.csv",
    filename: "nexuserp_warehouse_report.csv",
  },
  {
    title: "Қызметкерлер есебі",
    description: "Қызметкерлер, бөлім, лауазым, рөл және статус.",
    endpoint: "/reports/employees.csv",
    filename: "nexuserp_employees_report.csv",
  },
];

function FinanceBar({
  label,
  value,
  max,
  color,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const width = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span>{label}</span>
        <span>{value.toLocaleString()} ₸</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-white/5">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

function MetricCard({
  title,
  value,
  hint,
  tone = "text-white",
}: {
  title: string;
  value: string | number;
  hint: string;
  tone?: string;
}) {
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
  const [summary, setSummary] = useState<DashboardData | null>(null);
  const [reportSummary, setReportSummary] = useState<ReportSummary | null>(null);
  const [monthly, setMonthly] = useState<MonthlyFinance[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    Promise.all([
      api.get("/analytics/dashboard/"),
      api.get("/analytics/monthly-finance/"),
      api.get<ReportSummary>("/reports/summary/"),
    ])
      .then(([dashboard, monthlyFinance, reportsSummary]) => {
        setSummary(dashboard.data.data);
        setMonthly(monthlyFinance.data.data);
        setReportSummary(reportsSummary.data);
      })
      .catch((err: { response?: { status?: number } }) => {
        setError(
          `Аналитика API қатесі (${err.response?.status ?? "?"}). Backend-ті қайта іске қосыңыз.`
        );
      });
  }, []);

  async function downloadReport(endpoint: string, filename: string) {
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
      toast.error("Есеп жүктелмеді", "Backend API немесе рұқсатты тексеріңіз.");
    }
  }

  if (error) {
    return (
      <div>
        <PageHeader title="Аналитика & Есептер" description="KPI, қаржы динамикасы және CSV/PDF экспорт" />
        <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      </div>
    );
  }

  if (!summary) return <LoadingState label="Аналитика жүктелуде..." />;

  const maxBar = Math.max(
    ...monthly.flatMap((m) => [m.income, m.expense]),
    1
  );

  return (
    <div>
      <PageHeader
        title="Аналитика & Есептер"
        description="KPI, қаржы динамикасы, бизнес қорытынды және экспорт"
        action={
          <button onClick={() => window.print()} className="ghost-button px-4 py-2 text-sm">
            <Printer className="h-4 w-4" />
            Басып шығару / PDF
          </button>
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-4">
        <MetricCard title="Тапсырма орындалуы" value={`${summary.tasks.completion_rate}%`} hint="процестің аяқталуы" tone="text-brand-300" />
        <MetricCard title="Жалпы табыс" value={`${summary.finance.income.toLocaleString()} ₸`} hint="барлық табыс" tone="text-emerald-300" />
        <MetricCard title="Жалпы шығын" value={`${summary.finance.expense.toLocaleString()} ₸`} hint="барлық шығын" tone="text-red-300" />
        <MetricCard title="Төмен қалдық" value={summary.warehouse.low_stock} hint={`${summary.warehouse.products} өнім`} tone="text-amber-200" />
      </div>

      {reportSummary && (
        <section className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard title="Қызметкерлер" value={reportSummary.data.employees.active} hint={`барлығы ${reportSummary.data.employees.total}`} />
          <MetricCard title="Тапсырмалар" value={reportSummary.data.tasks.total} hint={`мерзімі өткен ${reportSummary.data.tasks.overdue}`} />
          <MetricCard title="Қойма қозғалыстары" value={reportSummary.data.warehouse.movements} hint="кіріс/шығыс тарихы" />
          <MetricCard title="Баланс" value={`${reportSummary.data.finance.balance.toLocaleString()} ₸`} hint="табыс - шығын" tone={reportSummary.data.finance.balance >= 0 ? "text-emerald-300" : "text-red-300"} />
        </section>
      )}

      <section className="premium-card p-6">
        <h3 className="mb-4 text-xl font-bold">Айлар бойынша қаржы динамикасы</h3>
        {monthly.length === 0 ? (
          <p className="text-sm text-gray-400">График үшін қаржы жазбаларын қосыңыз.</p>
        ) : (
          <div className="space-y-6">
            {monthly.map((m) => (
              <div key={m.month}>
                <p className="mb-2 text-sm font-medium text-gray-300">{m.month}</p>
                <div className="space-y-2">
                  <FinanceBar
                    label="Табыс"
                    value={m.income}
                    max={maxBar}
                    color="bg-emerald-500"
                  />
                  <FinanceBar
                    label="Шығын"
                    value={m.expense}
                    max={maxBar}
                    color="bg-red-500"
                  />
                </div>
              </div>
            ))}
          </div>
        )}
        <p className="mt-4 text-sm text-gray-400">
          Баланс: <span className="text-white">{summary.finance.balance.toLocaleString()} ₸</span>
        </p>
      </section>

      <section className="mt-6">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold">Экспорт орталығы</h2>
            <p className="text-sm text-gray-400">Есептерді CSV ретінде жүктеу немесе PDF ретінде басып шығару</p>
          </div>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {reports.map((report) => (
            <div key={report.endpoint} className="premium-card p-5">
              <div className="mb-4 flex items-start gap-3">
                <div className="rounded-2xl bg-brand-500/15 p-3">
                  <FileSpreadsheet className="h-5 w-5 text-brand-300" />
                </div>
                <div>
                  <h3 className="font-semibold">{report.title}</h3>
                  <p className="mt-1 text-sm text-gray-400">{report.description}</p>
                </div>
              </div>
              <button
                onClick={() => downloadReport(report.endpoint, report.filename)}
                className="premium-button px-4 py-2 text-sm"
              >
                <Download className="h-4 w-4" />
                CSV жүктеу
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
