"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowDownRight, ArrowUpRight, Pencil, Plus, Search, Trash2, X } from "lucide-react";
import { api } from "@/lib/api";
import type { FinanceEntry, PaginatedResponse } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { EmptyState, LoadingState } from "@/components/ui/StateBlock";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";

const DEFAULT_FORM = {
  entry_type: "income" as FinanceEntry["entry_type"],
  title: "",
  amount: "",
  category: "",
  description: "",
  entry_date: new Date().toISOString().slice(0, 10),
};

const QUICK_CATEGORIES = ["Сату", "Қойма", "Жалақы", "Кеңсе", "Көлік", "Маркетинг", "Басқа"];

function money(value: number) {
  return `${value.toLocaleString()} ₸`;
}

function FinanceMetric({
  title,
  value,
  hint,
  type,
}: {
  title: string;
  value: number;
  hint: string;
  type: "income" | "expense" | "balance";
}) {
  const positive = type === "income" || (type === "balance" && value >= 0);
  return (
    <div className="premium-card p-5">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-gray-400">{title}</p>
        <div
          className={
            positive
              ? "rounded-2xl bg-emerald-500/10 p-2 text-emerald-300"
              : "rounded-2xl bg-red-500/10 p-2 text-red-300"
          }
        >
          {positive ? <ArrowUpRight className="h-5 w-5" /> : <ArrowDownRight className="h-5 w-5" />}
        </div>
      </div>
      <p className={positive ? "text-3xl font-black text-emerald-300" : "text-3xl font-black text-red-300"}>
        {money(value)}
      </p>
      <p className="mt-1 text-xs text-gray-500">{hint}</p>
    </div>
  );
}

export default function FinancePage() {
  const { user } = useAuth();
  const toast = useToast();
  const [entries, setEntries] = useState<FinanceEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingEntry, setEditingEntry] = useState<FinanceEntry | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<FinanceEntry | null>(null);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<"all" | "income" | "expense">("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [loadError, setLoadError] = useState("");
  const [form, setForm] = useState(DEFAULT_FORM);

  const canEdit = user?.role === "admin" || user?.role === "manager";

  function load() {
    setLoading(true);
    setLoadError("");
    api
      .get<PaginatedResponse<FinanceEntry>>("/finance/entries/")
      .then((res) => setEntries(res.data.results))
      .catch(() => {
        setEntries([]);
        setLoadError("Қаржы деректері жүктелмеді. Backend логтарын немесе авторизацияны тексеріңіз.");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => load(), []);

  function resetForm() {
    setForm(DEFAULT_FORM);
    setEditingEntry(null);
    setShowForm(false);
  }

  function openCreateForm() {
    setEditingEntry(null);
    setForm(DEFAULT_FORM);
    setShowForm(true);
  }

  function openEditForm(entry: FinanceEntry) {
    setEditingEntry(entry);
    setForm({
      entry_type: entry.entry_type,
      title: entry.title,
      amount: entry.amount,
      category: entry.category || "",
      description: entry.description || "",
      entry_date: entry.entry_date,
    });
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const payload = {
        ...form,
        amount: form.amount,
      };
      if (editingEntry) {
        await api.patch(`/finance/entries/${editingEntry.id}/`, payload);
        toast.success("Қаржы жазбасы жаңартылды", form.title);
      } else {
        await api.post("/finance/entries/", payload);
        toast.success("Қаржы жазбасы қосылды", form.title);
      }
      resetForm();
      load();
    } catch {
      toast.error("Жазба сақталмады", "Сома, атау және рұқсатты тексеріңіз.");
    }
  }

  async function deleteEntry() {
    if (!deleteTarget) return;
    try {
      await api.delete(`/finance/entries/${deleteTarget.id}/`);
      toast.success("Қаржы жазбасы өшірілді", deleteTarget.title);
      setDeleteTarget(null);
      load();
    } catch {
      toast.error("Жазба өшірілмеді", "Бұл әрекетке рұқсат жоқ немесе сервер қатесі.");
    }
  }

  const categories = useMemo(
    () => Array.from(new Set(entries.map((entry) => entry.category).filter(Boolean))).sort(),
    [entries]
  );
  const categoryOptions = useMemo(
    () => Array.from(new Set([...QUICK_CATEGORIES, ...categories])).sort(),
    [categories]
  );

  const filteredEntries = entries.filter((entry) => {
    const text = `${entry.title} ${entry.category} ${entry.description}`.toLowerCase();
    const matchesQuery = text.includes(query.toLowerCase());
    const matchesType = typeFilter === "all" || entry.entry_type === typeFilter;
    const matchesCategory = categoryFilter === "all" || entry.category === categoryFilter;
    return matchesQuery && matchesType && matchesCategory;
  });

  const income = entries.filter((e) => e.entry_type === "income").reduce((s, e) => s + Number(e.amount), 0);
  const expense = entries.filter((e) => e.entry_type === "expense").reduce((s, e) => s + Number(e.amount), 0);
  const balance = income - expense;

  const filteredIncome = filteredEntries
    .filter((e) => e.entry_type === "income")
    .reduce((s, e) => s + Number(e.amount), 0);
  const filteredExpense = filteredEntries
    .filter((e) => e.entry_type === "expense")
    .reduce((s, e) => s + Number(e.amount), 0);

  const categorySummary = categories
    .map((category) => {
      const categoryEntries = entries.filter((entry) => entry.category === category);
      const totalIncome = categoryEntries
        .filter((entry) => entry.entry_type === "income")
        .reduce((sum, entry) => sum + Number(entry.amount), 0);
      const totalExpense = categoryEntries
        .filter((entry) => entry.entry_type === "expense")
        .reduce((sum, entry) => sum + Number(entry.amount), 0);
      return { category, totalIncome, totalExpense, balance: totalIncome - totalExpense };
    })
    .sort((a, b) => Math.abs(b.balance) - Math.abs(a.balance))
    .slice(0, 5);

  const monthlySummary = Array.from(
    entries.reduce((map, entry) => {
      const month = entry.entry_date.slice(0, 7);
      const current = map.get(month) || { month, income: 0, expense: 0 };
      if (entry.entry_type === "income") current.income += Number(entry.amount);
      else current.expense += Number(entry.amount);
      map.set(month, current);
      return map;
    }, new Map<string, { month: string; income: number; expense: number }>())
  )
    .map(([, value]) => value)
    .sort((a, b) => b.month.localeCompare(a.month))
    .slice(0, 6);

  const maxMonthly = Math.max(...monthlySummary.flatMap((item) => [item.income, item.expense]), 1);

  return (
    <div>
      <PageHeader
        title="Қаржы"
        description="Табыс, шығын, category breakdown және cashflow бақылау"
        action={
          canEdit ? (
            <button
              onClick={() => (showForm ? resetForm() : openCreateForm())}
              className="premium-button px-4 py-2 text-sm"
            >
              {showForm ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
              {showForm ? "Жабу" : "Жазба қосу"}
            </button>
          ) : undefined
        }
      />

      <section className="mb-6 grid gap-4 xl:grid-cols-4">
        <FinanceMetric title="Жалпы табыс" value={income} hint="барлық табыс жазбалары" type="income" />
        <FinanceMetric title="Жалпы шығын" value={expense} hint="барлық шығын жазбалары" type="expense" />
        <FinanceMetric title="Баланс" value={balance} hint="табыс - шығын" type="balance" />
        <div className="premium-card p-5">
          <p className="text-sm text-gray-400">Фильтрленген ақша ағымы</p>
          <p className="mt-3 text-2xl font-black">{money(filteredIncome - filteredExpense)}</p>
          <p className="mt-1 text-xs text-gray-500">
            {filteredEntries.length} жазба, {money(filteredIncome)} / {money(filteredExpense)}
          </p>
        </div>
      </section>

      <section className="mb-6 grid gap-4 xl:grid-cols-[1fr_1fr]">
        <div className="premium-card p-5">
          <h3 className="mb-4 text-lg font-bold">Категория бойынша талдау</h3>
          {categorySummary.length === 0 ? (
            <p className="text-sm text-gray-500">Категория қосылғанда талдау шығады.</p>
          ) : (
            <div className="space-y-3">
              {categorySummary.map((item) => (
                <div key={item.category} className="rounded-2xl border border-white/10 bg-white/5 p-3">
                  <div className="mb-2 flex justify-between text-sm">
                    <span className="font-medium">{item.category}</span>
                    <span className={item.balance >= 0 ? "text-emerald-300" : "text-red-300"}>
                      {money(item.balance)}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
                    <span>Табыс: {money(item.totalIncome)}</span>
                    <span>Шығын: {money(item.totalExpense)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="premium-card p-5">
          <h3 className="mb-4 text-lg font-bold">Айлық ақша ағымы</h3>
          {monthlySummary.length === 0 ? (
            <p className="text-sm text-gray-500">Айлық график үшін жазба қосыңыз.</p>
          ) : (
            <div className="space-y-4">
              {monthlySummary.map((item) => (
                <div key={item.month}>
                  <div className="mb-2 flex justify-between text-sm">
                    <span>{item.month}</span>
                    <span className={item.income - item.expense >= 0 ? "text-emerald-300" : "text-red-300"}>
                      {money(item.income - item.expense)}
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    <div className="h-2 overflow-hidden rounded-full bg-white/5">
                      <div
                        className="h-full rounded-full bg-emerald-500"
                        style={{ width: `${Math.round((item.income / maxMonthly) * 100)}%` }}
                      />
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-white/5">
                      <div
                        className="h-full rounded-full bg-red-500"
                        style={{ width: `${Math.round((item.expense / maxMonthly) * 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {loadError && (
        <p className="mb-4 rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {loadError}
        </p>
      )}

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative min-w-[260px] flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-500" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Атауы, категория, сипаттама бойынша іздеу..."
            className="premium-input py-2.5 pl-11 text-sm"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value as "all" | "income" | "expense")}
          className="premium-input max-w-[180px] py-2.5 text-sm"
        >
          <option value="all">Барлық түрі</option>
          <option value="income">Табыс</option>
          <option value="expense">Шығын</option>
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="premium-input max-w-[220px] py-2.5 text-sm"
        >
          <option value="all">Барлық категория</option>
          {categories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
      </div>

      {showForm && canEdit && (
        <form onSubmit={handleSubmit} className="premium-card mb-6 grid gap-3 p-5 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <h3 className="font-semibold">{editingEntry ? "Қаржы жазбасын өзгерту" : "Жаңа қаржы жазбасы"}</h3>
            <p className="text-sm text-gray-400">
              Категория және сипаттама қоссаңыз, аналитика нақтырақ болады.
            </p>
          </div>
          <select
            value={form.entry_type}
            onChange={(e) => setForm({ ...form, entry_type: e.target.value as FinanceEntry["entry_type"] })}
            className="premium-input"
          >
            <option value="income">Табыс</option>
            <option value="expense">Шығын</option>
          </select>
          <input
            placeholder="Атауы"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="premium-input"
            required
          />
          <input
            type="number"
            min="0"
            step="0.01"
            placeholder="Сома"
            value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })}
            className="premium-input"
            required
          />
          <input
            type="date"
            value={form.entry_date}
            onChange={(e) => setForm({ ...form, entry_date: e.target.value })}
            className="premium-input"
          />
          <div className="sm:col-span-2">
            <input
              list="finance-categories"
              placeholder="Категория"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              className="premium-input"
            />
            <datalist id="finance-categories">
              {categoryOptions.map((category) => (
                <option key={category} value={category} />
              ))}
            </datalist>
          </div>
          <textarea
            placeholder="Сипаттама / note"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="premium-input sm:col-span-2"
            rows={3}
          />
          <div className="flex flex-wrap gap-2 sm:col-span-2">
            <button type="submit" className="premium-button px-4 py-2 text-sm">
              {editingEntry ? "Өзгерісті сақтау" : "Сақтау"}
            </button>
            {editingEntry && (
              <button type="button" onClick={resetForm} className="ghost-button px-4 py-2 text-sm">
                Болдырмау
              </button>
            )}
          </div>
        </form>
      )}

      {loading ? (
        <LoadingState />
      ) : (
        filteredEntries.length === 0 ? (
          <EmptyState
            title="Қаржы жазбалары жоқ"
            description="Фильтрді өзгертіңіз немесе табыс/шығын қосыңыз."
          />
        ) : (
        <div className="glass-card overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-surface-border text-gray-400">
              <tr>
                <th className="px-4 py-3">Күні</th>
                <th className="px-4 py-3">Түрі</th>
                <th className="px-4 py-3">Атауы</th>
                <th className="px-4 py-3">Категория</th>
                <th className="px-4 py-3 text-right">Сома</th>
                {canEdit && <th className="px-4 py-3 text-right">Әрекет</th>}
              </tr>
            </thead>
            <tbody>
              {filteredEntries.map((e) => (
                <tr key={e.id} className="border-b border-surface-border/50 transition hover:bg-white/5">
                  <td className="px-4 py-3">{e.entry_date}</td>
                  <td className="px-4 py-3">
                    <Badge
                      label={e.entry_type === "income" ? "Табыс" : "Шығын"}
                      variant={e.entry_type}
                    />
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-medium">{e.title}</p>
                    {e.description && <p className="mt-1 line-clamp-1 text-xs text-gray-500">{e.description}</p>}
                  </td>
                  <td className="px-4 py-3 text-gray-400">{e.category || "—"}</td>
                  <td className={e.entry_type === "income" ? "px-4 py-3 text-right font-bold text-emerald-300" : "px-4 py-3 text-right font-bold text-red-300"}>
                    {Number(e.amount).toLocaleString()} ₸
                  </td>
                  {canEdit && (
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => openEditForm(e)}
                          className="rounded-lg border border-white/10 px-2 py-1 text-xs text-cyan-200 hover:bg-cyan-500/10"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => setDeleteTarget(e)}
                          className="rounded-lg border border-red-400/20 px-2 py-1 text-xs text-red-300 hover:bg-red-500/10"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        )
      )}

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Қаржы жазбасын өшіру"
        description={
          deleteTarget
            ? `"${deleteTarget.title}" жазбасын өшіргіңіз келе ме? Бұл әрекет қайтарылмайды.`
            : undefined
        }
        confirmLabel="Өшіру"
        onConfirm={deleteEntry}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
