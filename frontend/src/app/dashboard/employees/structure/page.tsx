"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { api } from "@/lib/api";
import type { Department, PaginatedResponse, Position } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/contexts/ToastContext";

export default function HrStructurePage() {
  const toast = useToast();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [showDeptForm, setShowDeptForm] = useState(false);
  const [showPositionForm, setShowPositionForm] = useState(false);
  const [deptForm, setDeptForm] = useState({ name: "", description: "" });
  const [positionForm, setPositionForm] = useState({
    title: "",
    department: "",
    base_salary: "",
  });

  const load = useCallback(() => {
    Promise.all([
      api.get<PaginatedResponse<Department>>("/employees/departments/"),
      api.get<PaginatedResponse<Position>>("/employees/positions/"),
    ]).then(([d, p]) => {
      setDepartments(d.data.results);
      setPositions(p.data.results);
    });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function createDepartment(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post("/employees/departments/", deptForm);
      setDeptForm({ name: "", description: "" });
      setShowDeptForm(false);
      toast.success("Бөлім қосылды", deptForm.name);
      load();
    } catch {
      toast.error("Бөлім қосылмады", "Атауы қайталанбауы керек.");
    }
  }

  async function createPosition(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post("/employees/positions/", {
        ...positionForm,
        department: Number(positionForm.department),
        base_salary: positionForm.base_salary || "0",
      });
      setPositionForm({ title: "", department: "", base_salary: "" });
      setShowPositionForm(false);
      toast.success("Лауазым қосылды", positionForm.title);
      load();
    } catch {
      toast.error("Лауазым қосылмады", "Бөлім және атауын тексеріңіз.");
    }
  }

  return (
    <div>
      <PageHeader
        title="HR Structure"
        description="Бөлімдер мен лауазымдарды басқару"
        action={
          <div className="flex gap-2">
            <button
              onClick={() => {
                setShowDeptForm(!showDeptForm);
                setShowPositionForm(false);
              }}
              className="inline-flex items-center gap-2 rounded-lg border border-surface-border px-4 py-2 text-sm hover:border-brand-500"
            >
              <Plus className="h-4 w-4" />
              Бөлім
            </button>
            <button
              onClick={() => {
                setShowPositionForm(!showPositionForm);
                setShowDeptForm(false);
              }}
              className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm hover:bg-brand-700"
            >
              <Plus className="h-4 w-4" />
              Лауазым
            </button>
          </div>
        }
      />

      {showDeptForm && (
        <form onSubmit={createDepartment} className="glass-card mb-4 grid gap-3 p-4 sm:grid-cols-2">
          <input
            placeholder="Бөлім атауы"
            value={deptForm.name}
            onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          />
          <input
            placeholder="Сипаттама"
            value={deptForm.description}
            onChange={(e) => setDeptForm({ ...deptForm, description: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
          />
          <button className="rounded-lg bg-brand-600 py-2 text-sm sm:col-span-2">
            Сақтау
          </button>
        </form>
      )}

      {showPositionForm && (
        <form onSubmit={createPosition} className="glass-card mb-4 grid gap-3 p-4 sm:grid-cols-3">
          <input
            placeholder="Лауазым атауы"
            value={positionForm.title}
            onChange={(e) => setPositionForm({ ...positionForm, title: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          />
          <select
            value={positionForm.department}
            onChange={(e) => setPositionForm({ ...positionForm, department: e.target.value })}
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
          <input
            type="number"
            placeholder="Base salary"
            value={positionForm.base_salary}
            onChange={(e) => setPositionForm({ ...positionForm, base_salary: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
          />
          <button className="rounded-lg bg-brand-600 py-2 text-sm sm:col-span-3">
            Сақтау
          </button>
        </form>
      )}

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="glass-card overflow-hidden">
          <div className="border-b border-surface-border px-4 py-3">
            <h3 className="font-semibold">Departments</h3>
          </div>
          <div className="divide-y divide-surface-border">
            {departments.map((department) => (
              <div key={department.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium">{department.name}</h4>
                    <p className="mt-1 text-sm text-gray-400">{department.description || "—"}</p>
                  </div>
                  <Badge
                    label={department.is_active ? "Active" : "Inactive"}
                    variant={department.is_active ? "approved" : "rejected"}
                  />
                </div>
                <div className="mt-3 flex gap-3 text-xs text-gray-500">
                  <span>{department.employees_count} employees</span>
                  <span>{department.positions_count} positions</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="glass-card overflow-hidden">
          <div className="border-b border-surface-border px-4 py-3">
            <h3 className="font-semibold">Positions</h3>
          </div>
          <div className="divide-y divide-surface-border">
            {positions.map((position) => (
              <div key={position.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium">{position.title}</h4>
                    <p className="mt-1 text-sm text-gray-400">{position.department_name}</p>
                  </div>
                  <Badge
                    label={position.is_active ? "Active" : "Inactive"}
                    variant={position.is_active ? "approved" : "rejected"}
                  />
                </div>
                <div className="mt-3 flex gap-3 text-xs text-gray-500">
                  <span>{position.employees_count} employees</span>
                  <span>{Number(position.base_salary).toLocaleString()} ₸ base</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
