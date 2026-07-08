"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { api } from "@/lib/api";
import type { Department, Employee, PaginatedResponse, Position } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/contexts/ToastContext";
import { usePermission } from "@/hooks/usePermission";
import { Perm, hasPermission } from "@/lib/permissions";
import { ROLE_LABELS } from "@/lib/auth";

export default function HrStructurePage() {
  const toast = useToast();
  const { can, permissions } = usePermission();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [showDeptForm, setShowDeptForm] = useState(false);
  const [showPositionForm, setShowPositionForm] = useState(false);
  const [deptForm, setDeptForm] = useState({ name: "", description: "" });
  const [positionForm, setPositionForm] = useState({
    title: "",
    department: "",
    base_salary: "",
  });
  const [assignManagerDept, setAssignManagerDept] = useState<number | null>(null);
  const [assignManagerId, setAssignManagerId] = useState("");
  const [removingManagerDept, setRemovingManagerDept] = useState<number | null>(null);

  const departmentManagerCandidates = useCallback(
    (department: Department) => {
      const deptEmployees = employees.filter((e) => e.department === department.id);
      return deptEmployees.filter(
        (e) => e.user.role === "employee" || e.id === department.manager_id
      );
    },
    [employees]
  );

  function openAssignManager(department: Department) {
    setAssignManagerDept(department.id);
    setAssignManagerId(department.manager_id ? String(department.manager_id) : "");
  }

  function closeAssignManager() {
    setAssignManagerDept(null);
    setAssignManagerId("");
  }

  const load = useCallback(() => {
    Promise.all([
      api.get<PaginatedResponse<Department>>("/employees/departments/"),
      api.get<PaginatedResponse<Position>>("/employees/positions/"),
      hasPermission(permissions, Perm.EMPLOYEES_VIEW_ALL) ||
        hasPermission(permissions, Perm.EMPLOYEES_VIEW_DEPARTMENT)
        ? api.get<PaginatedResponse<Employee>>("/employees/")
        : Promise.resolve({ data: { results: [] } }),
    ]).then(([d, p, e]) => {
      setDepartments(d.data.results);
      setPositions(p.data.results);
      setEmployees(e.data.results);
    });
  }, [permissions]);

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

  async function saveDepartmentManager(departmentId: number, managerId: string | null) {
    const removing = !managerId;
    try {
      await api.post(`/employees/departments/${departmentId}/assign-manager/`, {
        manager: managerId ? Number(managerId) : null,
      });
      toast.success(
        removing ? "Менеджер посттан алынды" : "Бөлім менеджері тағайындалды"
      );
      closeAssignManager();
      setRemovingManagerDept(null);
      load();
    } catch {
      toast.error(removing ? "Менеджерді алу мүмкін болмады" : "Менеджер тағайындалмады");
      setRemovingManagerDept(null);
    }
  }

  async function assignManager(departmentId: number) {
    await saveDepartmentManager(departmentId, assignManagerId || null);
  }

  async function removeDepartmentManager(department: Department) {
    setRemovingManagerDept(department.id);
    await saveDepartmentManager(department.id, null);
  }

  const canManageStructure = can(Perm.DEPARTMENTS_CREATE);

  return (
    <div>
      <PageHeader
        title="HR құрылымы"
        description="Бөлімдер мен лауазымдарды басқару"
        action={
          canManageStructure ? (
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
          ) : null
        }
      />

      {showDeptForm && can(Perm.DEPARTMENTS_CREATE) && (
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

      {showPositionForm && can(Perm.POSITIONS_CREATE) && (
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
            placeholder="Базалық жалақы"
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
            <h3 className="font-semibold">Бөлімдер</h3>
          </div>
          <div className="divide-y divide-surface-border">
            {departments.map((department) => (
              <div key={department.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium">{department.name}</h4>
                    <p className="mt-1 text-sm text-gray-400">{department.description || "—"}</p>
                    <p className="mt-2 text-xs text-cyan-200/80">
                      Менеджер: {department.manager_name || "тағайындалмаған"}
                    </p>
                  </div>
                  <Badge
                    label={department.is_active ? "Белсенді" : "Белсенді емес"}
                    variant={department.is_active ? "approved" : "rejected"}
                  />
                </div>
                <div className="mt-3 flex gap-3 text-xs text-gray-500">
                  <span>{department.employees_count} қызметкер</span>
                  <span>{department.positions_count} лауазым</span>
                </div>
                {can(Perm.DEPARTMENTS_ASSIGN_MANAGER) && (
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    {assignManagerDept === department.id ? (
                      <>
                        <select
                          value={assignManagerId}
                          onChange={(e) => setAssignManagerId(e.target.value)}
                          className="min-w-[180px] rounded-lg border border-surface-border bg-[#0f1117] px-2 py-1 text-xs"
                        >
                          <option value="">— Посттан алу —</option>
                          {departmentManagerCandidates(department).map((e) => (
                            <option key={e.id} value={e.id}>
                              {e.user.first_name || e.user.username}
                              {e.id === department.manager_id ? " (ағымдағы)" : ""}
                              {e.user.role === "manager" ? ` · ${ROLE_LABELS.manager}` : ""}
                            </option>
                          ))}
                        </select>
                        <button
                          onClick={() => assignManager(department.id)}
                          className="rounded-lg bg-brand-600 px-2 py-1 text-xs"
                        >
                          Сақтау
                        </button>
                        {!assignManagerId && department.manager_id ? (
                          <button
                            onClick={() => removeDepartmentManager(department)}
                            disabled={removingManagerDept === department.id}
                            className="rounded-lg border border-red-500/40 px-2 py-1 text-xs text-red-300 hover:bg-red-500/10 disabled:opacity-50"
                          >
                            {removingManagerDept === department.id ? "Алынуда..." : "Менеджерді алу"}
                          </button>
                        ) : null}
                        <button
                          onClick={closeAssignManager}
                          className="text-xs text-gray-400"
                        >
                          Бас тарту
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => openAssignManager(department)}
                          className="text-xs text-brand-400 hover:underline"
                        >
                          {department.manager_id ? "Менеджерді өзгерту" : "Менеджер тағайындау"}
                        </button>
                        {department.manager_id ? (
                          <button
                            onClick={() => removeDepartmentManager(department)}
                            disabled={removingManagerDept === department.id}
                            className="text-xs text-red-400 hover:underline disabled:opacity-50"
                          >
                            {removingManagerDept === department.id ? "Алынуда..." : "Менеджерді алу"}
                          </button>
                        ) : null}
                      </>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        <section className="glass-card overflow-hidden">
          <div className="border-b border-surface-border px-4 py-3">
            <h3 className="font-semibold">Лауазымдар</h3>
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
                    label={position.is_active ? "Белсенді" : "Белсенді емес"}
                    variant={position.is_active ? "approved" : "rejected"}
                  />
                </div>
                <div className="mt-3 flex gap-3 text-xs text-gray-500">
                  <span>{position.employees_count} қызметкер</span>
                  <span>{Number(position.base_salary).toLocaleString()} ₸ базалық</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
