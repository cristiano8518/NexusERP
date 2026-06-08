"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Briefcase, CheckCircle2, Mail, UserRound } from "lucide-react";
import { api } from "@/lib/api";
import type { EmployeeDetail } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";

const PRIORITY_LABELS: Record<string, string> = {
  low: "Төмен",
  medium: "Орташа",
  high: "Жоғары",
};

export default function EmployeeDetailPage() {
  const params = useParams<{ id: string }>();
  const [employee, setEmployee] = useState<EmployeeDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<EmployeeDetail>(`/employees/${params.id}/`)
      .then((res) => setEmployee(res.data))
      .finally(() => setLoading(false));
  }, [params.id]);

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

      <PageHeader title={fullName} description={`${employee.employee_id} · ${employee.position_title}`} />

      <div className="grid gap-6 xl:grid-cols-[1fr_1.4fr]">
        <section className="glass-card p-6">
          <div className="mb-6 flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-600/20">
              <UserRound className="h-8 w-8 text-brand-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">{fullName}</h2>
              <div className="mt-2 flex gap-2">
                <Badge label={employee.user.role} variant={employee.user.role} />
                <Badge
                  label={employee.is_active ? "Active" : "Inactive"}
                  variant={employee.is_active ? "approved" : "rejected"}
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
                <p className="text-xs text-gray-500">Hire date</p>
                <p className="font-medium">{employee.hire_date}</p>
              </div>
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-xs text-gray-500">Manager</p>
                <p className="font-medium">{employee.manager_name || "—"}</p>
              </div>
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-xs text-gray-500">Salary</p>
                <p className="font-medium">
                  {employee.salary ? `${Number(employee.salary).toLocaleString()} ₸` : "Жасырын"}
                </p>
              </div>
              <div className="rounded-xl bg-white/5 p-3">
                <p className="text-xs text-gray-500">Username</p>
                <p className="font-medium">@{employee.user.username}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-4">
            <div className="glass-card p-4">
              <p className="text-sm text-gray-400">Tasks</p>
              <p className="mt-1 text-2xl font-bold">{employee.task_summary.total}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-gray-400">In progress</p>
              <p className="mt-1 text-2xl font-bold text-blue-300">
                {employee.task_summary.in_progress}
              </p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-gray-400">Done</p>
              <p className="mt-1 text-2xl font-bold text-emerald-300">
                {employee.task_summary.done}
              </p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-gray-400">Rate</p>
              <p className="mt-1 text-2xl font-bold text-brand-400">
                {employee.task_summary.completion_rate}%
              </p>
            </div>
          </div>

          <div className="glass-card overflow-hidden">
            <div className="border-b border-surface-border px-4 py-3">
              <h3 className="font-semibold">Recent tasks</h3>
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
                        Deadline:{" "}
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
                  Бұл қызметкерге task берілмеген.
                </p>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
