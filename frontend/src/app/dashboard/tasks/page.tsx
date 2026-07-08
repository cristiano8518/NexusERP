"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { CalendarClock, CheckCircle2, Clock3, Pencil, Plus, Search, Trash2, X } from "lucide-react";
import { api } from "@/lib/api";
import type { Employee, PaginatedResponse, Task } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { EmptyState, LoadingState } from "@/components/ui/StateBlock";
import { useToast } from "@/contexts/ToastContext";
import { usePermission } from "@/hooks/usePermission";
import { Perm } from "@/lib/permissions";

const STATUS_LABELS: Record<string, string> = {
  draft: "Жоба",
  assigned: "Тапсырылды",
  in_progress: "Орындалуда",
  done: "Аяқталды",
  approved: "Бекітілді",
  rejected: "Қайтарылды",
};

const PRIORITY_LABELS: Record<string, string> = {
  low: "Төмен",
  medium: "Орташа",
  high: "Жоғары",
};

export default function TasksPage() {
  const { can, canAny } = usePermission();
  const toast = useToast();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Task | null>(null);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [form, setForm] = useState({
    title: "",
    description: "",
    priority: "medium",
    assignee: "",
    deadline: "",
  });

  const isManager = canAny(Perm.TASKS_CREATE, Perm.TASKS_UPDATE, Perm.TASKS_ASSIGN);

  function resetForm() {
    setForm({ title: "", description: "", priority: "medium", assignee: "", deadline: "" });
    setEditingTask(null);
    setShowForm(false);
  }

  function openCreateForm() {
    setEditingTask(null);
    setForm({ title: "", description: "", priority: "medium", assignee: "", deadline: "" });
    setShowForm(true);
  }

  function openEditForm(task: Task) {
    setEditingTask(task);
    setForm({
      title: task.title,
      description: task.description || "",
      priority: task.priority,
      assignee: task.assignee ? String(task.assignee) : "",
      deadline: task.deadline ? task.deadline.slice(0, 16) : "",
    });
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const loadTasks = useCallback(() => {
    setLoading(true);
    api
      .get<PaginatedResponse<Task>>("/tasks/")
      .then((res) => setTasks(res.data.results))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadTasks();
    if (isManager) {
      api.get<PaginatedResponse<Employee>>("/employees/").then((res) => {
        setEmployees(res.data.results);
      });
    }
  }, [loadTasks, isManager]);

  async function saveTask(e: React.FormEvent) {
    e.preventDefault();
    const payload = {
      title: form.title,
      description: form.description,
      priority: form.priority,
      assignee: form.assignee ? Number(form.assignee) : null,
      deadline: form.deadline || null,
    };
    try {
      if (editingTask) {
        await api.patch(`/tasks/${editingTask.id}/`, payload);
        toast.success("Тапсырма жаңартылды", form.title);
      } else {
        await api.post("/tasks/", payload);
        toast.success("Тапсырма жасалды", "Орындаушыға notification жіберілді.");
      }
      resetForm();
      loadTasks();
    } catch {
      toast.error("Тапсырма сақталмады", "Деректерді және рұқсаттарды тексеріңіз.");
    }
  }

  async function deleteTask() {
    if (!deleteTarget) return;
    try {
      await api.delete(`/tasks/${deleteTarget.id}/`);
      toast.success("Тапсырма өшірілді", deleteTarget.title);
      setDeleteTarget(null);
      loadTasks();
    } catch {
      toast.error("Тапсырма өшірілмеді", "Бұл әрекетке рұқсат жоқ немесе сервер қатесі.");
    }
  }

  async function transition(task: Task, status: string, note = "") {
    try {
      await api.post(`/tasks/${task.id}/transition/`, { status, note });
      toast.success("Статус өзгерді", task.title);
      loadTasks();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Жұмыс процесі ережесін тексеріңіз.";
      toast.error("Статус өзгермеді", msg);
    }
  }

  const filteredTasks = tasks.filter((task) => {
    const matchesQuery =
      task.title.toLowerCase().includes(query.toLowerCase()) ||
      task.description.toLowerCase().includes(query.toLowerCase()) ||
      (task.assignee_name || "").toLowerCase().includes(query.toLowerCase());
    const matchesStatus = statusFilter === "all" || task.status === statusFilter;
    return matchesQuery && matchesStatus;
  });

  const stats = {
    total: tasks.length,
    active: tasks.filter((t) => ["assigned", "in_progress", "rejected"].includes(t.status)).length,
    done: tasks.filter((t) => ["done", "approved"].includes(t.status)).length,
    overdue: tasks.filter((t) => t.is_overdue).length,
  };

  return (
    <div>
      <PageHeader
        title="Тапсырмалар"
        description="Менеджер → Қызметкер → Бекіту бизнес процесі"
        action={
          isManager ? (
            <button
              onClick={() => (showForm ? resetForm() : openCreateForm())}
              className="premium-button px-4 py-2 text-sm"
            >
              {showForm ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
              {showForm ? "Жабу" : "Жаңа тапсырма"}
            </button>
          ) : undefined
        }
      />

      <div className="mb-6 grid gap-3 sm:grid-cols-4">
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400">Барлығы</p>
          <p className="mt-1 text-2xl font-bold">{stats.total}</p>
        </div>
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400">Жұмыста</p>
          <p className="mt-1 text-2xl font-bold text-blue-300">{stats.active}</p>
        </div>
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400">Аяқталған</p>
          <p className="mt-1 text-2xl font-bold text-emerald-300">{stats.done}</p>
        </div>
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400">Мерзімі өтті</p>
          <p className="mt-1 text-2xl font-bold text-red-300">{stats.overdue}</p>
        </div>
      </div>

      <div className="mb-6 grid gap-3 md:grid-cols-2">
        <div className="glass-card p-4 text-sm text-gray-300">
          <span className="font-semibold text-cyan-200">Менеджер/Әкімші:</span>{" "}
          тапсырма құрады, өзгертеді, өшіреді және қызметкер жіберген жұмысты бекітеді немесе қайтарады.
        </div>
        <div className="glass-card p-4 text-sm text-gray-300">
          <span className="font-semibold text-emerald-200">Қызметкер:</span>{" "}
          тек өзіне берілген тапсырманы көреді, прогресті жаңартады, бастайды және тексеруге жібереді.
        </div>
      </div>

      {showForm && isManager && (
        <form onSubmit={saveTask} className="glass-card mb-6 space-y-4 p-5">
          <div>
            <h3 className="font-semibold">
              {editingTask ? "Тапсырманы өзгерту" : "Жаңа тапсырма"}
            </h3>
            <p className="text-sm text-gray-400">
              Менеджер тапсырманың атауын, орындаушысын, мерзімін және басымдығын басқарады.
            </p>
          </div>
          <input
            placeholder="Тапсырма атауы"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="premium-input"
            required
          />
          <textarea
            placeholder="Сипаттама"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="premium-input"
            rows={2}
          />
          <div className="flex flex-wrap gap-3">
            <select
              value={form.priority}
              onChange={(e) => setForm({ ...form, priority: e.target.value })}
              className="premium-input max-w-[180px]"
            >
              <option value="low">Төмен</option>
              <option value="medium">Орташа</option>
              <option value="high">Жоғары</option>
            </select>
            <select
              value={form.assignee}
              onChange={(e) => setForm({ ...form, assignee: e.target.value })}
              className="premium-input max-w-[260px]"
            >
              <option value="">Қызметкер таңдау</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.user.first_name || emp.user.username}
                </option>
              ))}
            </select>
            <input
              type="datetime-local"
              value={form.deadline}
              onChange={(e) => setForm({ ...form, deadline: e.target.value })}
              className="premium-input max-w-[240px]"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="submit" className="premium-button px-4 py-2 text-sm">
              {editingTask ? "Өзгерісті сақтау" : "Сақтау"}
            </button>
            {editingTask && (
              <button type="button" onClick={resetForm} className="ghost-button px-4 py-2 text-sm">
                Болдырмау
              </button>
            )}
          </div>
        </form>
      )}

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative min-w-[260px] flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
          <input
            placeholder="Тапсырма, орындаушы бойынша іздеу..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full rounded-lg border border-surface-border bg-[#0f1117] py-2 pl-9 pr-3 text-sm outline-none focus:border-brand-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2 text-sm"
        >
          <option value="all">Барлық статус</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <LoadingState />
      ) : (
        <div className="space-y-3">
          {filteredTasks.map((task) => (
            <div key={task.id} className="glass-card p-5 transition hover:border-brand-500/60">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <Link
                    href={`/dashboard/tasks/${task.id}`}
                    className="text-lg font-semibold transition hover:text-brand-400"
                  >
                    {task.title}
                  </Link>
                  {task.description && (
                    <p className="mt-1 line-clamp-2 text-sm text-gray-400">{task.description}</p>
                  )}
                  <div className="mt-3 flex flex-wrap gap-3 text-xs text-gray-500">
                    <span>Орындаушы: {task.assignee_name || "—"}</span>
                    {task.deadline && (
                      <span className={task.is_overdue ? "text-red-300" : ""}>
                        Мерзім: {new Date(task.deadline).toLocaleString("kk-KZ")}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge label={STATUS_LABELS[task.status] ?? task.status} variant={task.status} />
                  <Badge label={PRIORITY_LABELS[task.priority] ?? task.priority} variant={task.priority} />
                  {task.is_overdue && <Badge label="Мерзімі өтті" variant="rejected" />}
                </div>
              </div>
              <div className="mt-4">
                <div className="mb-1 flex justify-between text-xs text-gray-500">
                  <span>Прогресс</span>
                  <span>{task.progress}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-brand-500"
                    style={{ width: `${task.progress}%` }}
                  />
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {isManager && (
                  <>
                    <button
                      onClick={() => openEditForm(task)}
                      className="rounded-lg border border-white/10 px-3 py-1 text-xs text-cyan-200 transition hover:border-cyan-300/50 hover:bg-cyan-500/10"
                    >
                      <Pencil className="mr-1 inline h-3 w-3" />
                      Өзгерту
                    </button>
                    <button
                      onClick={() => setDeleteTarget(task)}
                      className="rounded-lg border border-red-400/20 px-3 py-1 text-xs text-red-300 transition hover:bg-red-500/10"
                    >
                      <Trash2 className="mr-1 inline h-3 w-3" />
                      Өшіру
                    </button>
                  </>
                )}
                {can(Perm.TASKS_UPDATE_OWN_PROGRESS) && task.status !== "approved" && (
                  <>
                    {["assigned", "rejected"].includes(task.status) && (
                      <button
                        onClick={() => transition(task, "in_progress")}
                        className="rounded-lg bg-blue-600/20 px-3 py-1 text-xs text-blue-300 hover:bg-blue-600/30"
                      >
                        <Clock3 className="mr-1 inline h-3 w-3" />
                        Жұмысты бастау
                      </button>
                    )}
                    {task.status === "in_progress" && (
                      <button
                        onClick={() => transition(task, "done")}
                        className="rounded-lg bg-emerald-600/20 px-3 py-1 text-xs text-emerald-300 hover:bg-emerald-600/30"
                      >
                        <CheckCircle2 className="mr-1 inline h-3 w-3" />
                        Орындадым
                      </button>
                    )}
                  </>
                )}
                {isManager && task.status === "done" && (
                  <>
                    <button
                      onClick={() => transition(task, "approved")}
                      className="rounded-lg bg-green-600/20 px-3 py-1 text-xs text-green-300"
                    >
                      Бекіту
                    </button>
                    <button
                      onClick={() => transition(task, "rejected", "Қайта өңдеу қажет.")}
                      className="rounded-lg bg-red-600/20 px-3 py-1 text-xs text-red-300"
                    >
                      Қайтару
                    </button>
                  </>
                )}
                <Link
                  href={`/dashboard/tasks/${task.id}`}
                  className="rounded-lg border border-surface-border px-3 py-1 text-xs text-gray-300 hover:border-brand-500"
                >
                  Толық ашу
                </Link>
              </div>
            </div>
          ))}
          {filteredTasks.length === 0 && (
            <EmptyState
              title="Тапсырмалар табылмады"
              description="Фильтрді өзгертіңіз немесе manager ретінде жаңа тапсырма қосыңыз."
              action={<CalendarClock className="mx-auto h-8 w-8 text-gray-600" />}
            />
          )}
        </div>
      )}

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Тапсырманы өшіру"
        description={
          deleteTarget
            ? `"${deleteTarget.title}" тапсырмасын өшіргіңіз келе ме? Бұл әрекет қайтарылмайды.`
            : undefined
        }
        confirmLabel="Өшіру"
        onConfirm={deleteTask}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
