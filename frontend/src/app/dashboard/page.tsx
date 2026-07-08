"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { usePermission } from "@/hooks/usePermission";
import { Perm, hasPermission } from "@/lib/permissions";
import { Badge } from "@/components/ui/Badge";
import type { PaginatedResponse, Task } from "@/lib/types";
import { BarChart3, CheckSquare, Package, Users } from "lucide-react";

type DashboardData = {
  employees: { total: number };
  tasks: { total: number; completed: number; in_progress: number; completion_rate: number };
  warehouse: { products: number; low_stock: number };
  finance: { income: number; expense: number; balance: number };
};

const TASK_COLUMNS = [
  { status: "assigned", title: "Тапсырылды", color: "border-amber-500/40" },
  { status: "in_progress", title: "Орындалуда", color: "border-blue-500/40" },
  { status: "done", title: "Тексеруде", color: "border-purple-500/40" },
  { status: "approved", title: "Бекітілді", color: "border-emerald-500/40" },
  { status: "rejected", title: "Қайтарылды", color: "border-red-500/40" },
];

const PRIORITY_LABELS: Record<string, string> = {
  low: "Төмен",
  medium: "Орташа",
  high: "Жоғары",
};

function KpiCard({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
}) {
  return (
    <div className="premium-card group overflow-hidden p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="mt-2 text-3xl font-black tracking-tight text-white">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-gray-500">{subtitle}</p>}
        </div>
        <div className="rounded-2xl bg-gradient-to-br from-brand-500/25 to-cyan-500/15 p-3 transition group-hover:scale-110">
          <Icon className="h-5 w-5 text-cyan-200" />
        </div>
      </div>
      <div className="mt-5 h-1 overflow-hidden rounded-full bg-white/5">
        <div className="h-full w-2/3 rounded-full bg-gradient-to-r from-brand-500 to-cyan-400" />
      </div>
    </div>
  );
}

function DashboardTaskBoard({ tasks }: { tasks: Task[] }) {
  return (
    <section className="mt-8">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Тапсырмалар тақтасы</h2>
          <p className="mt-1 text-sm text-gray-400">
            Компаниядағы тапсырмалар статусы бойынша live көрініс
          </p>
        </div>
        <Link
          href="/dashboard/tasks"
          className="ghost-button px-4 py-2 text-sm"
        >
          Толық тізім
        </Link>
      </div>

      <div className="grid gap-4 xl:grid-cols-5">
        {TASK_COLUMNS.map((column) => {
          const columnTasks = tasks.filter((task) => task.status === column.status).slice(0, 4);
          return (
            <div
              key={column.status}
              className={`min-h-[260px] rounded-3xl border ${column.color} bg-white/[0.055] p-4 shadow-xl shadow-black/20 backdrop-blur-xl`}
            >
              <div className="mb-4 flex items-center justify-between">
                <h3 className="font-semibold">{column.title}</h3>
                <span className="rounded-full border border-white/10 bg-white/10 px-2 py-0.5 text-xs text-gray-300">
                  {tasks.filter((task) => task.status === column.status).length}
                </span>
              </div>

              <div className="space-y-3">
                {columnTasks.map((task) => (
                  <Link
                    key={task.id}
                    href={`/dashboard/tasks/${task.id}`}
                    className="block rounded-2xl border border-white/10 bg-black/20 p-3 transition duration-300 hover:-translate-y-0.5 hover:border-brand-400/50 hover:bg-white/[0.08]"
                  >
                    <div className="mb-2 flex items-start justify-between gap-2">
                      <p className="line-clamp-2 text-sm font-medium">{task.title}</p>
                      {task.is_overdue && <Badge label="!" variant="rejected" />}
                    </div>
                    <div className="mb-2 flex flex-wrap gap-2">
                      <Badge
                        label={PRIORITY_LABELS[task.priority] ?? task.priority}
                        variant={task.priority}
                      />
                      <span className="text-xs text-gray-500">{task.progress}%</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-brand-500 to-cyan-400"
                        style={{ width: `${task.progress}%` }}
                      />
                    </div>
                    <p className="mt-2 text-xs text-gray-500">{task.assignee_name || "—"}</p>
                  </Link>
                ))}
                {columnTasks.length === 0 && (
                  <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.025] p-4 text-center text-xs text-gray-500">
                    Бос
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { can, permissions } = usePermission();
  const [data, setData] = useState<DashboardData | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskCount, setTaskCount] = useState<number | null>(null);
  const [apiError, setApiError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const canViewAnalytics =
      hasPermission(permissions, Perm.ANALYTICS_VIEW_COMPANY) ||
      hasPermission(permissions, Perm.ANALYTICS_VIEW_DEPARTMENT);

    if (canViewAnalytics) {
      api
        .get("/analytics/dashboard/")
        .then((res) => {
          if (!cancelled) {
            setData(res.data.data);
            setApiError("");
          }
        })
        .catch((err: { response?: { status?: number; data?: unknown } }) => {
          if (!cancelled) {
            setData(null);
            setApiError(
              `API қатесі (${err.response?.status ?? "?"}). Backend қайта іске қосыңыз: docker compose up --build`
            );
          }
        });
    } else if (!cancelled) {
      setData(null);
      setApiError("");
    }

    api
      .get<PaginatedResponse<Task>>("/tasks/")
      .then((res) => {
        if (!cancelled) {
          setTasks(res.data.results);
          setTaskCount(res.data.count ?? res.data.results.length);
        }
      })
      .catch(() => {
        if (!cancelled) setTaskCount(0);
      });

    return () => {
      cancelled = true;
    };
  }, [user, permissions]);

  const isEmployee = !can(Perm.ANALYTICS_VIEW_COMPANY) && !can(Perm.ANALYTICS_VIEW_DEPARTMENT);

  return (
    <div>
      <div className="mb-8 overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-r from-white/[0.12] via-white/[0.07] to-transparent p-6 shadow-2xl shadow-black/20 backdrop-blur-2xl">
      <p className="mb-3 text-xs font-semibold uppercase tracking-[0.28em] text-cyan-200">
        Бүгінгі шолу
      </p>
      <h1 className="text-3xl font-black tracking-tight md:text-4xl">
        Сәлем, {user?.first_name || user?.username}!
      </h1>
      <p className="mt-2 max-w-2xl text-gray-400">
        {isEmployee
          ? "Сіздің тапсырмаларыңызды «Тапсырмалар» бөлімінен басқарыңыз."
          : "Компания көрсеткіштерінің қысқаша шолуы"}
      </p>
      </div>

      {apiError && (
        <p className="mb-4 rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {apiError}
        </p>
      )}

      {isEmployee ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2">
            <KpiCard
              title="Менің тапсырмаларым"
              value={taskCount ?? "—"}
              icon={CheckSquare}
            />
            <Link
              href="/dashboard/tasks"
              className="premium-card flex items-center justify-center p-5 text-cyan-200"
            >
              Тапсырмаларға өту →
            </Link>
          </div>
          <DashboardTaskBoard tasks={tasks} />
        </>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard title="Қызметкерлер" value={data?.employees.total ?? "—"} icon={Users} />
            <KpiCard
              title="Тапсырмалар"
              value={data?.tasks.total ?? "—"}
              subtitle={data ? `${data.tasks.completion_rate}% аяқталды` : undefined}
              icon={CheckSquare}
            />
            <KpiCard
              title="Тауарлар"
              value={data?.warehouse.products ?? "—"}
              subtitle={data ? `${data.warehouse.low_stock} төмен қалдық` : undefined}
              icon={Package}
            />
            <KpiCard
              title="Баланс"
              value={data ? `${data.finance.balance.toLocaleString()} ₸` : "—"}
              subtitle={data ? `Табыс: ${data.finance.income.toLocaleString()} ₸` : undefined}
              icon={BarChart3}
            />
          </div>
          <DashboardTaskBoard tasks={tasks} />
        </>
      )}
    </div>
  );
}
