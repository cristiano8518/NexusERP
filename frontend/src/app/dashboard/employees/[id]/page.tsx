"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowRightLeft,
  Briefcase,
  CheckCircle2,
  Mail,
  ShieldBan,
  ShieldCheck,
  TrendingUp,
  UserMinus,
  UserPlus,
  UserRound,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Department, EmployeeDetail, PaginatedResponse, Position } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { useToast } from "@/contexts/ToastContext";
import { usePermission } from "@/hooks/usePermission";
import { Perm } from "@/lib/permissions";
import { ROLE_LABELS } from "@/lib/auth";

const PRIORITY_LABELS: Record<string, string> = {
  low: "Төмен",
  medium: "Орташа",
  high: "Жоғары",
};

export default function EmployeeDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const toast = useToast();
  const { can, permissions } = usePermission();
  const [employee, setEmployee] = useState<EmployeeDetail | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [confirmAction, setConfirmAction] = useState<string | null>(null);
  const [transferDept, setTransferDept] = useState("");
  const [transferPos, setTransferPos] = useState("");
  const [promoteDept, setPromoteDept] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      api.get<EmployeeDetail>(`/employees/${params.id}/`),
      can(Perm.EMPLOYEES_TRANSFER) || can(Perm.EMPLOYEES_PROMOTE_MANAGER)
        ? api.get<PaginatedResponse<Department>>("/employees/departments/")
        : Promise.resolve({ data: { results: [] as Department[] } }),
      can(Perm.EMPLOYEES_TRANSFER)
        ? api.get<PaginatedResponse<Position>>("/employees/positions/")
        : Promise.resolve({ data: { results: [] as Position[] } }),
    ])
      .then(([emp, dept, pos]) => {
        setEmployee(emp.data);
        setDepartments(dept.data.results);
        setPositions(pos.data.results);
        setPromoteDept(String(emp.data.department));
      })
      .catch(() => setEmployee(null))
      .finally(() => setLoading(false));
  }, [params.id, permissions]);

  useEffect(() => {
    load();
  }, [load]);

  async function runAction(action: string) {
    if (!employee) return;
    try {
      if (action === "promote") {
        await api.post(`/employees/${employee.id}/promote/`, {
          department: Number(promoteDept),
        });
        toast.success("Менеджерге көтерілді");
      } else if (action === "demote") {
        await api.post(`/employees/${employee.id}/demote/`);
        toast.success("Қызметкерге түсірілді");
      } else if (action === "block") {
        await api.post(`/employees/${employee.id}/block/`);
        toast.success("Қызметкер блокталды");
      } else if (action === "unblock") {
        await api.post(`/employees/${employee.id}/unblock/`);
        toast.success("Қызметкер блоктан шығарылды");
      } else if (action === "delete") {
        await api.delete(`/employees/${employee.id}/`);
        toast.success("Қызметкер жойылды");
        router.push("/dashboard/employees");
        return;
      } else if (action === "transfer") {
        await api.post(`/employees/${employee.id}/transfer/`, {
          department: Number(transferDept),
          position: Number(transferPos),
        });
        toast.success("Бөлім ауыстырылды");
      }
      setConfirmAction(null);
      load();
    } catch {
      toast.error("Әрекет орындалмады", "Недостаточно прав доступа немесе деректер қате.");
    }
  }

  if (loading) return <p className="text-gray-400">Жүктелуде...</p>;
  if (!employee) return <p className="text-red-300">Қызметкер табылмады.</p>;

  const fullName =
    `${employee.user.first_name || ""} ${employee.user.last_name || ""}`.trim() ||
    employee.user.username;

  return (
    <div>
      <Link
        href="/dashboard/employees"
        className="mb-4 inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white"
      >
        <ArrowLeft className="h-4 w-4" />
        Қызметкерлерге қайту
      </Link>

      <PageHeader
        title={fullName}
        description={`${employee.employee_id} · ${employee.position_title}`}
        action={
          can(Perm.SYSTEM_MANAGE) || can(Perm.EMPLOYEES_UPDATE) ? (
            <div className="flex flex-wrap gap-2">
              {can(Perm.EMPLOYEES_PROMOTE_MANAGER) && employee.user.role === "employee" && (
                <button
                  onClick={() => setConfirmAction("promote")}
                  className="inline-flex items-center gap-2 rounded-lg bg-emerald-600/20 px-3 py-2 text-xs text-emerald-200"
                >
                  <UserPlus className="h-4 w-4" />
                  Менеджерге көтеру
                </button>
              )}
              {can(Perm.EMPLOYEES_DEMOTE_MANAGER) && employee.user.role === "manager" && (
                <button
                  onClick={() => setConfirmAction("demote")}
                  className="inline-flex items-center gap-2 rounded-lg bg-amber-600/20 px-3 py-2 text-xs text-amber-200"
                >
                  <UserMinus className="h-4 w-4" />
                  Қызметкерге түсіру
                </button>
              )}
              {can(Perm.EMPLOYEES_BLOCK) && !employee.is_blocked && employee.user.role !== "admin" && (
                <button
                  onClick={() => setConfirmAction("block")}
                  className="inline-flex items-center gap-2 rounded-lg bg-red-600/20 px-3 py-2 text-xs text-red-200"
                >
                  <ShieldBan className="h-4 w-4" />
                  Блоктау
                </button>
              )}
              {can(Perm.EMPLOYEES_BLOCK) && employee.is_blocked && (
                <button
                  onClick={() => setConfirmAction("unblock")}
                  className="inline-flex items-center gap-2 rounded-lg bg-emerald-600/20 px-3 py-2 text-xs text-emerald-200"
                >
                  <ShieldCheck className="h-4 w-4" />
                  Блоктан шығару
                </button>
              )}
            </div>
          ) : null
        }
      />

      {confirmAction === "promote" && (
        <div className="glass-card mb-4 flex flex-wrap items-end gap-3 p-4">
          <div>
            <label className="text-xs text-gray-400">Бөлім менеджері</label>
            <select
              value={promoteDept}
              onChange={(e) => setPromoteDept(e.target.value)}
              className="mt-1 block rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2 text-sm"
            >
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={() => runAction("promote")}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm"
          >
            Растау
          </button>
        </div>
      )}

      {can(Perm.EMPLOYEES_TRANSFER) && employee.user.role === "employee" && (
        <div className="glass-card mb-4 grid gap-3 p-4 sm:grid-cols-4">
          <p className="sm:col-span-4 text-sm font-medium text-gray-300">
            <ArrowRightLeft className="mr-2 inline h-4 w-4" />
            Бөлім ауыстыру (тек директор)
          </p>
          <select
            value={transferDept}
            onChange={(e) => {
              setTransferDept(e.target.value);
              setTransferPos("");
            }}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2 text-sm"
          >
            <option value="">Жаңа бөлім</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          <select
            value={transferPos}
            onChange={(e) => setTransferPos(e.target.value)}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2 text-sm"
            disabled={!transferDept}
          >
            <option value="">Лауазым</option>
            {positions
              .filter((p) => String(p.department) === transferDept)
              .map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title}
                </option>
              ))}
          </select>
          <button
            onClick={() => setConfirmAction("transfer")}
            disabled={!transferDept || !transferPos}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm disabled:opacity-40"
          >
            Ауыстыру
          </button>
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1fr_1.4fr]">
        <section className="glass-card p-6">
          <div className="mb-6 flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-600/20">
              <UserRound className="h-8 w-8 text-brand-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">{fullName}</h2>
              <div className="mt-2 flex gap-2">
                <Badge label={ROLE_LABELS[employee.user.role]} variant={employee.user.role} />
                <Badge
                  label={employee.is_blocked ? "Блокта" : employee.is_active ? "Белсенді" : "Белсенді емес"}
                  variant={employee.is_blocked ? "rejected" : "approved"}
                />
              </div>
            </div>
          </div>

          <div className="space-y-4 text-sm">
            <div className="flex items-center gap-3">
              <Mail className="h-4 w-4 text-gray-500" />
              <span>{employee.user.email}</span>
            </div>
            <div className="flex items-center gap-3">
              <Briefcase className="h-4 w-4 text-gray-500" />
              <span>
                {employee.department_name} · {employee.position_title}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 pt-4">
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-xs text-gray-500">Қабылданған күн</p>
                <p className="font-medium">{employee.hire_date}</p>
              </div>
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-xs text-gray-500">Жетекші</p>
                <p className="font-medium">{employee.manager_name || "—"}</p>
              </div>
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-xs text-gray-500">Жалақы</p>
                <p className="font-medium">
                  {employee.salary ? `${Number(employee.salary).toLocaleString()} ₸` : "Жасырын"}
                </p>
              </div>
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-xs text-gray-500">Жүктеме</p>
                <p className="font-medium">
                  {employee.workload?.active_tasks ?? 0} белсенді тапсырма
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-4">
            <div className="glass-card p-4">
              <p className="text-sm text-gray-400">Тапсырмалар</p>
              <p className="mt-1 text-2xl font-bold">{employee.task_summary.total}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-gray-400">Орындалуда</p>
              <p className="mt-1 text-2xl font-bold text-blue-300">
                {employee.task_summary.in_progress}
              </p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-gray-400">Аяқталған</p>
              <p className="mt-1 text-2xl font-bold text-emerald-300">
                {employee.task_summary.done}
              </p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-gray-400">Көрсеткіш</p>
              <p className="mt-1 text-2xl font-bold text-brand-400">
                {employee.task_summary.completion_rate}%
              </p>
            </div>
          </div>

          <div className="glass-card overflow-hidden">
            <div className="border-b border-surface-border px-4 py-3">
              <h3 className="font-semibold">Соңғы тапсырмалар</h3>
            </div>
            <div className="divide-y divide-surface-border">
              {employee.recent_tasks.map((task) => (
                <Link
                  key={task.id}
                  href={`/dashboard/tasks/${task.id}`}
                  className="block p-4 transition hover:bg-white/5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium">{task.title}</p>
                      <p className="mt-1 text-xs text-gray-500">
                        Мерзім:{" "}
                        {task.deadline
                          ? new Date(task.deadline).toLocaleString("kk-KZ")
                          : "—"}
                      </p>
                    </div>
                    <div className="flex flex-wrap justify-end gap-2">
                      <Badge label={task.status_display} variant={task.status} />
                      <Badge
                        label={PRIORITY_LABELS[task.priority] ?? task.priority}
                        variant={task.priority}
                      />
                    </div>
                  </div>
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/5">
                    <div
                      className="h-full rounded-full bg-brand-500"
                      style={{ width: `${task.progress}%` }}
                    />
                  </div>
                </Link>
              ))}
              {employee.recent_tasks.length === 0 && (
                <p className="p-6 text-center text-sm text-gray-500">
                  Бұл қызметкерге тапсырма берілмеген.
                </p>
              )}
            </div>
          </div>
        </section>
      </div>

      <ConfirmDialog
        open={!!confirmAction && confirmAction !== "promote"}
        title="Әрекетті растау"
        description={`"${fullName}" үшін әрекетті орындауға сенімдісіз бе?`}
        onConfirm={() => confirmAction && runAction(confirmAction)}
        onCancel={() => setConfirmAction(null)}
      />
    </div>
  );
}
