"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Building2, Plus } from "lucide-react";
import { api } from "@/lib/api";
import type { Department, Employee, PaginatedResponse, Position } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";

export default function EmployeesPage() {
  const { user } = useAuth();
  const toast = useToast();
  const [items, setItems] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    role: "employee",
    employee_id: "",
    department: "",
    position: "",
    hire_date: new Date().toISOString().slice(0, 10),
    salary: "",
  });

  const isAdmin = user?.role === "admin";

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      api.get<PaginatedResponse<Employee>>("/employees/"),
      api.get<PaginatedResponse<Department>>("/employees/departments/"),
      api.get<PaginatedResponse<Position>>("/employees/positions/"),
    ])
      .then(([emp, dept, pos]) => {
        setItems(emp.data.results);
        setDepartments(dept.data.results);
        setPositions(pos.data.results);
      })
      .catch(() => setError("Деректерді жүктеу мүмкін болмады."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filteredPositions = positions.filter(
    (p) => !form.department || String(p.department) === form.department
  );

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post("/employees/", {
        ...form,
        department: Number(form.department),
        position: Number(form.position),
        salary: form.salary,
      });
      setShowForm(false);
      toast.success("Қызметкер қосылды", form.username);
      load();
    } catch {
      setError("Қызметкерді қосу мүмкін болмады. Деректерді тексеріңіз.");
      toast.error("Қызметкер қосылмады", "Логин/email немесе employee ID қайталанбауы керек.");
    }
  }

  return (
    <div>
      <PageHeader
        title="Қызметкерлер"
        description="HR — персоналды басқару"
        action={
          <div className="flex flex-wrap gap-2">
            <Link
              href="/dashboard/employees/structure"
              className="inline-flex items-center gap-2 rounded-lg border border-surface-border px-4 py-2 text-sm text-gray-300 hover:border-brand-500"
            >
              <Building2 className="h-4 w-4" />
              HR Structure
            </Link>
            {isAdmin && (
              <button
                onClick={() => setShowForm(!showForm)}
                className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm hover:bg-brand-700"
              >
                <Plus className="h-4 w-4" />
                Қызметкер қосу
              </button>
            )}
          </div>
        }
      />

      {error && (
        <p className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {showForm && isAdmin && (
        <form
          onSubmit={handleCreate}
          className="glass-card mb-6 grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3"
        >
          <input
            placeholder="Логин"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          />
          <input
            placeholder="Email"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          />
          <input
            placeholder="Пароль"
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          />
          <input
            placeholder="Аты"
            value={form.first_name}
            onChange={(e) => setForm({ ...form, first_name: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
          />
          <input
            placeholder="Тегі"
            value={form.last_name}
            onChange={(e) => setForm({ ...form, last_name: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
          />
          <input
            placeholder="Employee ID (мыс. EMP-002)"
            value={form.employee_id}
            onChange={(e) => setForm({ ...form, employee_id: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          />
          <select
            value={form.department}
            onChange={(e) => setForm({ ...form, department: e.target.value, position: "" })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          >
            <option value="">Бөлім</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          <select
            value={form.position}
            onChange={(e) => setForm({ ...form, position: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          >
            <option value="">Лауазым</option>
            {filteredPositions.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
          </select>
          <select
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
          >
            <option value="employee">Қызметкер</option>
            <option value="manager">Менеджер</option>
            <option value="admin">Админ</option>
          </select>
          <input
            type="date"
            value={form.hire_date}
            onChange={(e) => setForm({ ...form, hire_date: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
          />
          <input
            placeholder="Жалақы"
            type="number"
            value={form.salary}
            onChange={(e) => setForm({ ...form, salary: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          />
          <button
            type="submit"
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm hover:bg-brand-700 sm:col-span-2 lg:col-span-3"
          >
            Сақтау
          </button>
        </form>
      )}

      {loading ? (
        <p className="text-gray-400">Жүктелуде...</p>
      ) : (
        <>
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          <div className="glass-card p-4">
            <p className="text-sm text-gray-400">Қызметкерлер</p>
            <p className="mt-1 text-2xl font-bold">{items.length}</p>
          </div>
          <div className="glass-card p-4">
            <p className="text-sm text-gray-400">Бөлімдер</p>
            <p className="mt-1 text-2xl font-bold">{departments.length}</p>
          </div>
          <div className="glass-card p-4">
            <p className="text-sm text-gray-400">Лауазымдар</p>
            <p className="mt-1 text-2xl font-bold">{positions.length}</p>
          </div>
        </div>

        <div className="glass-card overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-surface-border text-gray-400">
              <tr>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">Аты</th>
                <th className="px-4 py-3">Бөлім</th>
                <th className="px-4 py-3">Лауазым</th>
                <th className="px-4 py-3">Рөл</th>
                <th className="px-4 py-3">Жалақы</th>
              </tr>
            </thead>
            <tbody>
              {items.map((emp) => (
                <tr key={emp.id} className="border-b border-surface-border/50 hover:bg-white/5">
                  <td className="px-4 py-3 font-mono text-xs">{emp.employee_id}</td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/dashboard/employees/${emp.id}`}
                      className="font-medium hover:text-brand-400"
                    >
                      {emp.user.first_name || emp.user.username} {emp.user.last_name}
                    </Link>
                    <span className="block text-xs text-gray-500">{emp.user.email}</span>
                  </td>
                  <td className="px-4 py-3">{emp.department_name}</td>
                  <td className="px-4 py-3">{emp.position_title}</td>
                  <td className="px-4 py-3">
                    <Badge label={emp.user.role} variant={emp.user.role} />
                  </td>
                  <td className="px-4 py-3">
                    {emp.salary ? `${Number(emp.salary).toLocaleString()} ₸` : "Жасырын"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        </>
      )}
    </div>
  );
}
