"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  Clock3,
  MessageSquare,
  Pencil,
  RotateCcw,
  Send,
  Trash2,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Employee, PaginatedResponse, TaskDetail } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { PageHeader } from "@/components/ui/PageHeader";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";

const STATUS_LABELS: Record<string, string> = {
  draft: "Жоба",
  assigned: "Тапсырылды",
  in_progress: "Орындалуда",
  done: "Тексеруге жіберілді",
  approved: "Бекітілді",
  rejected: "Қайтарылды",
};

const PRIORITY_LABELS: Record<string, string> = {
  low: "Төмен",
  medium: "Орташа",
  high: "Жоғары",
};

function formatDate(value: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("kk-KZ");
}

function WorkflowStep({
  label,
  active,
  done,
}: {
  label: string;
  active?: boolean;
  done?: boolean;
}) {
  return (
    <div className="flex flex-1 items-center gap-2">
      <div
        className={`flex h-8 w-8 items-center justify-center rounded-full border text-xs ${
          done
            ? "border-emerald-500 bg-emerald-500/20 text-emerald-300"
            : active
              ? "border-brand-500 bg-brand-500/20 text-brand-300"
              : "border-surface-border text-gray-500"
        }`}
      >
        {done ? "✓" : "•"}
      </div>
      <span className={active || done ? "text-sm text-white" : "text-sm text-gray-500"}>
        {label}
      </span>
    </div>
  );
}

export default function TaskDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const toast = useToast();
  const [task, setTask] = useState<TaskDetail | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState("");
  const [note, setNote] = useState("");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [editForm, setEditForm] = useState({
    title: "",
    description: "",
    priority: "medium",
    assignee: "",
    deadline: "",
  });

  const isManager = user?.role === "admin" || user?.role === "manager";
  const isEmployee = user?.role === "employee";

  const loadTask = useCallback(() => {
    setLoading(true);
    api
      .get<TaskDetail>(`/tasks/${params.id}/`)
      .then((res) => {
        setTask(res.data);
        setProgress(res.data.progress);
      })
      .catch(() => setError("Тапсырманы жүктеу мүмкін болмады."))
      .finally(() => setLoading(false));
  }, [params.id]);

  useEffect(() => {
    loadTask();
    if (isManager) {
      api.get<PaginatedResponse<Employee>>("/employees/").then((res) => {
        setEmployees(res.data.results);
      });
    }
  }, [loadTask, isManager]);

  function startEdit() {
    if (!task) return;
    setEditForm({
      title: task.title,
      description: task.description || "",
      priority: task.priority,
      assignee: task.assignee ? String(task.assignee) : "",
      deadline: task.deadline ? task.deadline.slice(0, 16) : "",
    });
    setEditing(true);
  }

  async function saveTask(e: React.FormEvent) {
    e.preventDefault();
    if (!task) return;
    try {
      await api.patch(`/tasks/${task.id}/`, {
        title: editForm.title,
        description: editForm.description,
        priority: editForm.priority,
        assignee: editForm.assignee ? Number(editForm.assignee) : null,
        deadline: editForm.deadline || null,
      });
      setEditing(false);
      toast.success("Тапсырма жаңартылды", editForm.title);
      loadTask();
    } catch {
      toast.error("Өзгеріс сақталмады", "Manager/Admin рұқсаттарын және деректерді тексеріңіз.");
    }
  }

  async function deleteTask() {
    if (!task) return;
    try {
      await api.delete(`/tasks/${task.id}/`);
      toast.success("Тапсырма өшірілді", task.title);
      router.push("/dashboard/tasks");
    } catch {
      toast.error("Тапсырма өшірілмеді", "Бұл әрекетке рұқсат жоқ немесе сервер қатесі.");
    }
  }

  async function transition(status: string) {
    if (!task) return;
    setError("");
    try {
      const { data } = await api.post(`/tasks/${task.id}/transition/`, {
        status,
        note,
      });
      setTask(data.task);
      setNote("");
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Статусты өзгерту мүмкін болмады.";
      setError(message);
    }
  }

  async function saveProgress() {
    if (!task) return;
    const { data } = await api.patch<TaskDetail>(`/tasks/${task.id}/`, {
      progress,
    });
    setTask({ ...task, progress: data.progress });
    loadTask();
  }

  async function addComment(e: React.FormEvent) {
    e.preventDefault();
    if (!task || !comment.trim()) return;
    await api.post(`/tasks/${task.id}/comments/`, { message: comment.trim() });
    setComment("");
    loadTask();
  }

  if (loading) return <p className="text-gray-400">Жүктелуде...</p>;
  if (!task) return <p className="text-red-300">{error || "Тапсырма табылмады."}</p>;

  const stepIndex = ["assigned", "in_progress", "done", "approved"].indexOf(task.status);

  return (
    <div>
      <Link
        href="/dashboard/tasks"
        className="mb-4 inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white"
      >
        <ArrowLeft className="h-4 w-4" />
        Тапсырмаларға қайту
      </Link>

      <PageHeader
        title={task.title}
        description="Тапсырма карточкасы, орындау тарихы және approval процесі"
        action={
          isManager ? (
            <div className="flex flex-wrap gap-2">
              <button onClick={startEdit} className="ghost-button px-4 py-2 text-sm">
                <Pencil className="h-4 w-4" />
                Өзгерту
              </button>
              <button
                onClick={() => setConfirmDelete(true)}
                className="inline-flex items-center gap-2 rounded-2xl border border-red-400/20 bg-red-500/10 px-4 py-2 text-sm font-medium text-red-200 transition hover:bg-red-500/20"
              >
                <Trash2 className="h-4 w-4" />
                Өшіру
              </button>
            </div>
          ) : undefined
        }
      />

      {error && (
        <p className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {editing && isManager && (
        <form onSubmit={saveTask} className="glass-card mb-6 space-y-4 p-5">
          <div>
            <h3 className="font-semibold">Тапсырманы өзгерту</h3>
            <p className="text-sm text-gray-400">
              Employee progress/status бөлек workflow арқылы өзгереді.
            </p>
          </div>
          <input
            value={editForm.title}
            onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
            className="premium-input"
            required
          />
          <textarea
            value={editForm.description}
            onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
            className="premium-input"
            rows={3}
          />
          <div className="flex flex-wrap gap-3">
            <select
              value={editForm.priority}
              onChange={(e) => setEditForm({ ...editForm, priority: e.target.value })}
              className="premium-input max-w-[180px]"
            >
              <option value="low">Төмен</option>
              <option value="medium">Орташа</option>
              <option value="high">Жоғары</option>
            </select>
            <select
              value={editForm.assignee}
              onChange={(e) => setEditForm({ ...editForm, assignee: e.target.value })}
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
              value={editForm.deadline}
              onChange={(e) => setEditForm({ ...editForm, deadline: e.target.value })}
              className="premium-input max-w-[240px]"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="submit" className="premium-button px-4 py-2 text-sm">
              Сақтау
            </button>
            <button type="button" onClick={() => setEditing(false)} className="ghost-button px-4 py-2 text-sm">
              Болдырмау
            </button>
          </div>
        </form>
      )}

      <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <div className="space-y-6">
          <section className="glass-card p-6">
            <div className="mb-4 flex flex-wrap gap-2">
              <Badge label={STATUS_LABELS[task.status] ?? task.status} variant={task.status} />
              <Badge label={PRIORITY_LABELS[task.priority] ?? task.priority} variant={task.priority} />
              {task.is_overdue && <Badge label="Deadline өтті" variant="rejected" />}
            </div>

            <p className="whitespace-pre-wrap text-gray-300">
              {task.description || "Сипаттама жоқ."}
            </p>

            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              <div>
                <p className="text-xs text-gray-500">Орындаушы</p>
                <p className="font-medium">{task.assignee_name || "—"}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Deadline</p>
                <p className={task.is_overdue ? "font-medium text-red-300" : "font-medium"}>
                  {formatDate(task.deadline)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Жасалған</p>
                <p className="font-medium">{formatDate(task.created_at)}</p>
              </div>
            </div>

            <div className="mt-6">
              <div className="mb-2 flex justify-between text-sm">
                <span className="text-gray-400">Прогресс</span>
                <span>{task.progress}%</span>
              </div>
              <div className="h-3 overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-brand-500"
                  style={{ width: `${task.progress}%` }}
                />
              </div>
            </div>
          </section>

          <section className="glass-card p-6">
            <h3 className="mb-4 font-semibold">Workflow</h3>
            <div className="grid gap-4 md:grid-cols-4">
              {["Тапсырылды", "Орындалуда", "Тексеруде", "Бекітілді"].map((label, index) => (
                <WorkflowStep
                  key={label}
                  label={label}
                  active={index === Math.max(stepIndex, 0)}
                  done={stepIndex > index || task.status === "approved"}
                />
              ))}
            </div>

            <div className="mt-6 flex flex-wrap gap-2">
              {isEmployee && ["assigned", "rejected"].includes(task.status) && (
                <button
                  onClick={() => transition("in_progress")}
                  className="inline-flex items-center gap-2 rounded-lg bg-blue-600/20 px-4 py-2 text-sm text-blue-300 hover:bg-blue-600/30"
                >
                  <Clock3 className="h-4 w-4" />
                  Жұмысты бастау
                </button>
              )}
              {isEmployee && task.status === "in_progress" && (
                <button
                  onClick={() => transition("done")}
                  className="inline-flex items-center gap-2 rounded-lg bg-emerald-600/20 px-4 py-2 text-sm text-emerald-300 hover:bg-emerald-600/30"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  Тексеруге жіберу
                </button>
              )}
              {isManager && task.status === "done" && (
                <>
                  <button
                    onClick={() => transition("approved")}
                    className="inline-flex items-center gap-2 rounded-lg bg-green-600/20 px-4 py-2 text-sm text-green-300 hover:bg-green-600/30"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    Бекіту
                  </button>
                  <button
                    onClick={() => transition("rejected")}
                    className="inline-flex items-center gap-2 rounded-lg bg-red-600/20 px-4 py-2 text-sm text-red-300 hover:bg-red-600/30"
                  >
                    <XCircle className="h-4 w-4" />
                    Қайтару
                  </button>
                </>
              )}
            </div>

            {(isManager || task.status === "done") && (
              <textarea
                placeholder="Approval note / қайтару себебі..."
                value={note}
                onChange={(e) => setNote(e.target.value)}
                className="mt-4 w-full rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2 text-sm outline-none focus:border-brand-500"
                rows={3}
              />
            )}
          </section>

          <section className="glass-card p-6">
            <h3 className="mb-4 flex items-center gap-2 font-semibold">
              <MessageSquare className="h-4 w-4" />
              Комментарийлер
            </h3>
            <form onSubmit={addComment} className="mb-4 flex gap-2">
              <input
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Комментарий жазу..."
                className="flex-1 rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2 text-sm outline-none focus:border-brand-500"
              />
              <button
                type="submit"
                className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm hover:bg-brand-700"
              >
                <Send className="h-4 w-4" />
                Жіберу
              </button>
            </form>
            <div className="space-y-3">
              {task.comments.map((item) => (
                <div key={item.id} className="rounded-xl bg-white/5 p-3">
                  <div className="mb-1 flex justify-between text-xs text-gray-500">
                    <span>{item.author_name || "System"}</span>
                    <span>{formatDate(item.created_at)}</span>
                  </div>
                  <p className="text-sm text-gray-200">{item.message}</p>
                </div>
              ))}
              {task.comments.length === 0 && (
                <p className="text-sm text-gray-500">Комментарий жоқ.</p>
              )}
            </div>
          </section>
        </div>

        <aside className="space-y-6">
          <section className="glass-card p-6">
            <h3 className="mb-4 font-semibold">Employee progress</h3>
            <input
              type="range"
              min={0}
              max={100}
              value={progress}
              onChange={(e) => setProgress(Number(e.target.value))}
              className="w-full"
              disabled={!isEmployee || task.status !== "in_progress"}
            />
            <div className="mt-2 flex items-center justify-between text-sm">
              <span className="text-gray-400">{progress}%</span>
              {isEmployee && task.status === "in_progress" && (
                <button
                  onClick={saveProgress}
                  className="rounded-lg border border-surface-border px-3 py-1 text-xs hover:border-brand-500"
                >
                  Сақтау
                </button>
              )}
            </div>
          </section>

          <section className="glass-card p-6">
            <h3 className="mb-4 flex items-center gap-2 font-semibold">
              <RotateCcw className="h-4 w-4" />
              Activity history
            </h3>
            <div className="space-y-4">
              {task.activities.map((activity) => (
                <div key={activity.id} className="border-l border-surface-border pl-4">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium">{activity.action_display}</p>
                    <span className="text-xs text-gray-500">{formatDate(activity.created_at)}</span>
                  </div>
                  <p className="text-xs text-gray-500">
                    {activity.actor_name || "System"}
                    {activity.from_status && activity.to_status
                      ? ` · ${STATUS_LABELS[activity.from_status] ?? activity.from_status} → ${
                          STATUS_LABELS[activity.to_status] ?? activity.to_status
                        }`
                      : ""}
                  </p>
                  {activity.message && (
                    <p className="mt-1 text-sm text-gray-300">{activity.message}</p>
                  )}
                </div>
              ))}
              {task.activities.length === 0 && (
                <p className="text-sm text-gray-500">Әрекет тарихы жоқ.</p>
              )}
            </div>
          </section>
        </aside>
      </div>
      <ConfirmDialog
        open={confirmDelete}
        title="Тапсырманы өшіру"
        description={`"${task.title}" тапсырмасын өшіргіңіз келе ме? Бұл әрекет қайтарылмайды.`}
        confirmLabel="Өшіру"
        onConfirm={deleteTask}
        onCancel={() => setConfirmDelete(false)}
      />
    </div>
  );
}
