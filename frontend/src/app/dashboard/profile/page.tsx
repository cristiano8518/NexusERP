"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  AtSign,
  BadgeCheck,
  BriefcaseBusiness,
  CalendarDays,
  CheckCircle2,
  Clock3,
  LogOut,
  Mail,
  Phone,
  Save,
  Shield,
  Sparkles,
  UserRound,
} from "lucide-react";
import { api, type User } from "@/lib/api";
import { ROLE_LABELS } from "@/lib/auth";
import type { EmployeeDetail } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";
import { LoadingState } from "@/components/ui/StateBlock";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";

type ProfileResponse = {
  success: boolean;
  user: User;
  employee_profile: EmployeeDetail | null;
};

const ROLE_LOGIC: Record<User["role"], string[]> = {
  admin: [
    "Барлық модульдерді толық басқарады",
    "Қызметкерлерді құрады, өзгертеді және өшіреді",
    "Қауіпсіздік логтарын және salary ақпаратын көре алады",
  ],
  manager: [
    "Тапсырмаларды құрады, өзгертеді және өшіреді",
    "Қызметкер жұмысын бекітеді немесе қайтарады",
    "HR, қойма, қаржы және есептерді басқарады",
  ],
  employee: [
    "Тек өзіне берілген тапсырмаларды көреді",
    "Прогресті жаңартады және жұмысты тексеруге жібереді",
    "Пікір жазып, жұмыс процесі арқылы жұмыс істейді",
  ],
};

function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("kk-KZ", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

function StatCard({
  label,
  value,
  tone = "text-white",
}: {
  label: string;
  value: string | number;
  tone?: string;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-gray-500">{label}</p>
      <p className={`mt-3 text-3xl font-black ${tone}`}>{value}</p>
    </div>
  );
}

export default function ProfilePage() {
  const { user, logout, refreshUser } = useAuth();
  const toast = useToast();
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
  });

  useEffect(() => {
    api
      .get<ProfileResponse>("/auth/me/")
      .then((res) => {
        setProfile(res.data);
        setForm({
          first_name: res.data.user.first_name || "",
          last_name: res.data.user.last_name || "",
          email: res.data.user.email || "",
          phone: res.data.user.phone || "",
        });
      })
      .catch(() => setLoadError("Профиль деректері жүктелмеді. Қайта кіріп көріңіз."))
      .finally(() => setLoading(false));
  }, []);

  const currentUser = profile?.user || user;
  const employee = profile?.employee_profile || null;
  const initials = useMemo(() => {
    const source =
      `${currentUser?.first_name || ""} ${currentUser?.last_name || ""}`.trim() ||
      currentUser?.username ||
      "N";
    return source
      .split(" ")
      .map((part) => part[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
  }, [currentUser]);

  const fullName =
    `${currentUser?.first_name || ""} ${currentUser?.last_name || ""}`.trim() ||
    currentUser?.username ||
    "Пайдаланушы";

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const { data } = await api.patch<{ success: boolean; user: User }>("/auth/me/", form);
      setProfile((current) => (current ? { ...current, user: data.user } : current));
      await refreshUser();
      toast.success("Профиль жаңартылды", "Негізгі ақпарат сақталды.");
    } catch {
      toast.error("Профиль сақталмады", "Электрондық пошта бос емес болуы мүмкін немесе сервер қатесі.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <LoadingState label="Профиль жүктелуде..." />;
  }

  if (loadError) {
    return (
      <div>
        <PageHeader title="Профиль" description="Аккаунт деректері" />
        <p className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {loadError}
        </p>
      </div>
    );
  }

  if (!currentUser) {
    return <LoadingState label="Пайдаланушы дерегі дайындалуда..." />;
  }

  const taskSummary = employee?.task_summary;

  return (
    <div>
      <PageHeader
        title="Профиль"
        description="Аккаунт, role, HR карточка және жеке жұмыс статистикасы"
      />

      <section className="relative mb-6 overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-brand-500/20 via-purple-500/10 to-cyan-500/10 p-6 shadow-2xl shadow-black/25 backdrop-blur-2xl">
        <div className="absolute right-8 top-8 h-36 w-36 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-5">
            <div className="orbital-ring flex h-24 w-24 items-center justify-center rounded-[2rem] text-3xl font-black shadow-2xl shadow-brand-950/40">
              {initials}
            </div>
            <div>
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <Badge label={ROLE_LABELS[currentUser.role]} variant={currentUser.role} />
                <span className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-200">
                  Белсенді аккаунт
                </span>
              </div>
              <h1 className="text-4xl font-black tracking-tight gradient-text">{fullName}</h1>
              <p className="mt-2 flex items-center gap-2 text-sm text-gray-300">
                <AtSign className="h-4 w-4 text-cyan-200" />
                {currentUser.username}
              </p>
            </div>
          </div>

          <button
            onClick={logout}
            className="inline-flex items-center justify-center gap-2 rounded-2xl border border-red-400/20 bg-red-500/10 px-5 py-3 text-sm font-semibold text-red-200 transition hover:bg-red-500/20"
          >
            <LogOut className="h-4 w-4" />
            Аккаунттан шығу
          </button>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <form onSubmit={saveProfile} className="premium-card p-6">
            <div className="mb-5 flex items-center gap-3">
              <div className="rounded-2xl bg-cyan-500/10 p-3 text-cyan-200">
                <UserRound className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Жеке ақпарат</h2>
                <p className="text-sm text-gray-400">Аты-жөніңіз, электрондық пошта және телефон нөмірі</p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block">
                <span className="mb-1 block text-sm text-gray-400">Аты</span>
                <input
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                  className="premium-input"
                  placeholder="Аты"
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-sm text-gray-400">Тегі</span>
                <input
                  value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                  className="premium-input"
                  placeholder="Тегі"
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-sm text-gray-400">Электрондық пошта</span>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="premium-input"
                  placeholder="name@nexuserp.local"
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-sm text-gray-400">Телефон</span>
                <input
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  className="premium-input"
                  placeholder="+7 777 000 00 00"
                />
              </label>
            </div>

            <button type="submit" disabled={saving} className="premium-button mt-5">
              <Save className="h-4 w-4" />
              {saving ? "Сақталуда..." : "Өзгерісті сақтау"}
            </button>
          </form>

          <section className="premium-card p-6">
            <div className="mb-5 flex items-center gap-3">
              <div className="rounded-2xl bg-purple-500/10 p-3 text-purple-200">
                <BriefcaseBusiness className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold">HR карточка</h2>
                <p className="text-sm text-gray-400">Бөлім, лауазым және қызметкер статусы</p>
              </div>
            </div>

            {employee ? (
              <div className="grid gap-4 md:grid-cols-2">
                <StatCard label="Қызметкер ID" value={employee.employee_id} />
                <StatCard label="Статус" value={employee.is_active ? "Белсенді" : "Белсенді емес"} tone="text-emerald-200" />
                <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Бөлім</p>
                  <p className="mt-3 text-lg font-bold">{employee.department_name || "—"}</p>
                </div>
                <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Лауазым</p>
                  <p className="mt-3 text-lg font-bold">{employee.position_title || "—"}</p>
                </div>
                <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Жетекші</p>
                  <p className="mt-3 text-lg font-bold">{employee.manager_name || "—"}</p>
                </div>
                <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Жұмысқа қабылданған күн</p>
                  <p className="mt-3 text-lg font-bold">{formatDate(employee.hire_date)}</p>
                </div>
                {employee.salary && (
                  <div className="rounded-3xl border border-emerald-400/20 bg-emerald-500/10 p-4 md:col-span-2">
                    <p className="text-xs uppercase tracking-[0.2em] text-emerald-300/70">Жалақы</p>
                    <p className="mt-3 text-2xl font-black text-emerald-200">
                      {Number(employee.salary).toLocaleString()} ₸
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-6 text-center">
                <p className="font-semibold text-gray-200">HR карточка әлі байланыспаған</p>
                <p className="mt-2 text-sm text-gray-500">
                  Әкімші қызметкер профилін Қызметкерлер бөлімінен жасай алады.
                </p>
              </div>
            )}
          </section>
        </div>

        <aside className="space-y-6">
          <section className="premium-card p-6">
            <div className="mb-5 flex items-center gap-3">
              <div className="rounded-2xl bg-brand-500/10 p-3 text-brand-200">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Рөл логикасы</h2>
                <p className="text-sm text-gray-400">{ROLE_LABELS[currentUser.role]} мүмкіндіктері</p>
              </div>
            </div>
            <div className="space-y-3">
              {ROLE_LOGIC[currentUser.role].map((item) => (
                <div key={item} className="flex gap-3 rounded-2xl border border-white/10 bg-white/5 p-3">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />
                  <p className="text-sm text-gray-300">{item}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="premium-card p-6">
            <div className="mb-5 flex items-center gap-3">
              <div className="rounded-2xl bg-cyan-500/10 p-3 text-cyan-200">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Жұмыс статистикасы</h2>
                <p className="text-sm text-gray-400">Тапсырма нәтижелерінің қысқаша көрінісі</p>
              </div>
            </div>

            {taskSummary ? (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <StatCard label="Барлығы" value={taskSummary.total} />
                  <StatCard label="Аяқталу %" value={`${taskSummary.completion_rate}%`} tone="text-cyan-200" />
                  <StatCard label="Орындалуда" value={taskSummary.in_progress} tone="text-blue-200" />
                  <StatCard label="Бекітілді" value={taskSummary.approved} tone="text-emerald-200" />
                </div>
                <div className="mt-5 h-3 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-brand-500 to-cyan-400"
                    style={{ width: `${taskSummary.completion_rate}%` }}
                  />
                </div>
              </>
            ) : (
              <p className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-gray-400">
                Тапсырма статистикасы HR карточкамен бірге шығады.
              </p>
            )}
          </section>

          <section className="premium-card p-6">
            <h2 className="mb-4 text-xl font-bold">Аккаунт деректері</h2>
            <div className="space-y-3 text-sm">
              <div className="flex items-center gap-3 rounded-2xl bg-white/5 p-3">
                <Mail className="h-4 w-4 text-cyan-200" />
                <span className="text-gray-300">{currentUser.email || "Электрондық пошта жоқ"}</span>
              </div>
              <div className="flex items-center gap-3 rounded-2xl bg-white/5 p-3">
                <Phone className="h-4 w-4 text-cyan-200" />
                <span className="text-gray-300">{currentUser.phone || "Телефон жоқ"}</span>
              </div>
              <div className="flex items-center gap-3 rounded-2xl bg-white/5 p-3">
                <CalendarDays className="h-4 w-4 text-cyan-200" />
                <span className="text-gray-300">Тіркелген күні: {formatDate(currentUser.date_joined)}</span>
              </div>
              <div className="flex items-center gap-3 rounded-2xl bg-white/5 p-3">
                <BadgeCheck className="h-4 w-4 text-cyan-200" />
                <span className="text-gray-300">Пайдаланушы ID: #{currentUser.id}</span>
              </div>
            </div>
          </section>

          <Link href="/dashboard/tasks" className="premium-card block p-6">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-emerald-500/10 p-3 text-emerald-200">
                <Clock3 className="h-5 w-5" />
              </div>
              <div>
                <h2 className="font-bold">Менің тапсырмаларым</h2>
                <p className="text-sm text-gray-400">Процесс пен прогресті басқару</p>
              </div>
            </div>
          </Link>
        </aside>
      </div>
    </div>
  );
}
