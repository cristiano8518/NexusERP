"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowDownCircle, ArrowUpCircle, Plus } from "lucide-react";
import { api } from "@/lib/api";
import type { Category, PaginatedResponse, Product, StockMovement } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { EmptyState, LoadingState } from "@/components/ui/StateBlock";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";

type Tab = "products" | "movements";

export default function WarehousePage() {
  const { user } = useAuth();
  const toast = useToast();
  const [tab, setTab] = useState<Tab>("products");
  const [products, setProducts] = useState<Product[]>([]);
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [showProductForm, setShowProductForm] = useState(false);
  const [showMoveForm, setShowMoveForm] = useState(false);
  const [error, setError] = useState("");
  const [productForm, setProductForm] = useState({
    sku: "",
    name: "",
    category: "",
    min_stock_level: "5",
    price: "0",
  });
  const [moveForm, setMoveForm] = useState({
    product: "",
    movement_type: "in",
    quantity: "",
    unit_price: "",
    note: "",
    auto_create_finance: true,
  });

  const canEdit = user?.role === "admin" || user?.role === "manager";

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      api.get<PaginatedResponse<Product>>("/warehouse/products/"),
      api.get<PaginatedResponse<StockMovement>>("/warehouse/movements/"),
      api.get<PaginatedResponse<Category>>("/warehouse/categories/"),
    ])
      .then(([p, m, c]) => {
        setProducts(p.data.results);
        setMovements(m.data.results);
        setCategories(c.data.results);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function createProduct(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/warehouse/products/", {
        ...productForm,
        category: Number(productForm.category),
      });
      setShowProductForm(false);
      toast.success("Тауар қосылды", productForm.name);
      load();
    } catch {
      toast.error("Тауар қосылмады", "SKU немесе категорияны тексеріңіз.");
    }
  }

  async function createMovement(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/warehouse/movements/", {
        product: Number(moveForm.product),
        movement_type: moveForm.movement_type,
        quantity: moveForm.quantity,
        unit_price: moveForm.unit_price || undefined,
        note: moveForm.note,
        auto_create_finance: moveForm.auto_create_finance,
      });
      setShowMoveForm(false);
      setMoveForm({
        product: "",
        movement_type: "in",
        quantity: "",
        unit_price: "",
        note: "",
        auto_create_finance: true,
      });
      toast.success("Қойма операциясы сақталды", "Қаржы интеграциясы қолданылды.");
      load();
    } catch (err: unknown) {
      const data = (err as { response?: { data?: { errors?: Record<string, string[]>; quantity?: string[]; detail?: string } } })?.response?.data;
      const msg =
        data?.errors?.quantity?.[0] ||
        data?.quantity?.[0] ||
        data?.detail ||
        "Операцияны сақтау мүмкін болмады.";
      setError(msg);
      toast.error("Операция сақталмады", msg);
    }
  }

  const selectedProduct = products.find((p) => String(p.id) === moveForm.product);
  const movementTotal =
    Number(moveForm.quantity || 0) *
    Number(moveForm.unit_price || selectedProduct?.price || 0);

  return (
    <div>
      <PageHeader
        title="Қойма"
        description="Тауарлар, қалдықтар, кіріс/шығыс"
        action={
          canEdit ? (
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setShowProductForm(!showProductForm);
                  setShowMoveForm(false);
                }}
                className="inline-flex items-center gap-2 rounded-lg border border-surface-border px-3 py-2 text-sm hover:border-brand-500"
              >
                <Plus className="h-4 w-4" />
                Тауар
              </button>
              <button
                onClick={() => {
                  setShowMoveForm(!showMoveForm);
                  setShowProductForm(false);
                }}
                className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-3 py-2 text-sm hover:bg-brand-700"
              >
                Кіріс/Шығыс
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

      <div className="mb-4 flex gap-2">
        {(["products", "movements"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-lg px-4 py-2 text-sm ${
              tab === t ? "bg-brand-600/20 text-brand-400" : "text-gray-400 hover:bg-white/5"
            }`}
          >
            {t === "products" ? "Тауарлар" : "Операциялар"}
          </button>
        ))}
      </div>

      {showProductForm && canEdit && (
        <form onSubmit={createProduct} className="glass-card mb-4 grid gap-3 p-4 sm:grid-cols-2">
          <input
            placeholder="SKU"
            value={productForm.sku}
            onChange={(e) => setProductForm({ ...productForm, sku: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          />
          <input
            placeholder="Атауы"
            value={productForm.name}
            onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          />
          <select
            value={productForm.category}
            onChange={(e) => setProductForm({ ...productForm, category: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          >
            <option value="">Категория</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <input
            type="number"
            placeholder="Бағасы"
            value={productForm.price}
            onChange={(e) => setProductForm({ ...productForm, price: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
          />
          <input
            type="number"
            placeholder="Минимум қалдық"
            value={productForm.min_stock_level}
            onChange={(e) => setProductForm({ ...productForm, min_stock_level: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
          />
          <button type="submit" className="rounded-lg bg-brand-600 py-2 text-sm sm:col-span-2">
            Тауарды сақтау
          </button>
        </form>
      )}

      {showMoveForm && canEdit && (
        <form onSubmit={createMovement} className="glass-card mb-4 grid gap-3 p-4 sm:grid-cols-2">
          <select
            value={moveForm.product}
            onChange={(e) => {
              const product = products.find((p) => String(p.id) === e.target.value);
              setMoveForm({
                ...moveForm,
                product: e.target.value,
                unit_price: product?.price || "",
              });
            }}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          >
            <option value="">Тауар</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.quantity})
              </option>
            ))}
          </select>
          <select
            value={moveForm.movement_type}
            onChange={(e) => setMoveForm({ ...moveForm, movement_type: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
          >
            <option value="in">Кіріс</option>
            <option value="out">Шығыс</option>
          </select>
          <input
            type="number"
            placeholder="Саны"
            value={moveForm.quantity}
            onChange={(e) => setMoveForm({ ...moveForm, quantity: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
            required
          />
          <input
            type="number"
            placeholder="Бірлік бағасы"
            value={moveForm.unit_price}
            onChange={(e) => setMoveForm({ ...moveForm, unit_price: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
          />
          <input
            placeholder="Ескертпе"
            value={moveForm.note}
            onChange={(e) => setMoveForm({ ...moveForm, note: e.target.value })}
            className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2"
          />
          <label className="flex items-center gap-2 rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2 text-sm text-gray-300">
            <input
              type="checkbox"
              checked={moveForm.auto_create_finance}
              onChange={(e) =>
                setMoveForm({ ...moveForm, auto_create_finance: e.target.checked })
              }
            />
            Қаржы жазбасын автоматты жасау
          </label>
          <div className="rounded-lg border border-surface-border bg-[#0f1117] px-3 py-2 text-sm">
            Жалпы сома:{" "}
            <span className="font-semibold text-brand-400">
              {movementTotal.toLocaleString()} ₸
            </span>
          </div>
          <button type="submit" className="rounded-lg bg-brand-600 py-2 text-sm sm:col-span-2">
            Операцияны сақтау
          </button>
        </form>
      )}

      {loading ? (
        <LoadingState />
      ) : tab === "products" ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {products.map((p) => (
            <Link
              key={p.id}
              href={`/dashboard/warehouse/products/${p.id}`}
              className="glass-card block p-4 transition hover:border-brand-500/60"
            >
              <div className="flex items-start justify-between">
                <h3 className="font-semibold">{p.name}</h3>
                {p.is_low_stock && <Badge label="Төмен" variant="high" />}
              </div>
              <p className="mt-1 font-mono text-xs text-gray-500">{p.sku}</p>
              <p className="mt-2 text-sm text-gray-400">{p.category_name}</p>
              <div className="mt-4 flex justify-between text-sm">
                <span>
                  Қалдық: <strong className="text-white">{p.quantity}</strong>
                </span>
                <span className="text-brand-400">{Number(p.price).toLocaleString()} ₸</span>
              </div>
              <div className="mt-2 flex justify-between text-xs text-gray-500">
                <span>Қойма құны</span>
                <span>{Number(p.inventory_value).toLocaleString()} ₸</span>
              </div>
            </Link>
          ))}
          {products.length === 0 && (
            <EmptyState
              title="Тауарлар жоқ"
              description="Қойма жұмысын бастау үшін бірінші тауар қосыңыз."
            />
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {movements.map((m) => (
            <div
              key={m.id}
              className="glass-card flex items-center justify-between gap-4 p-4 text-sm"
            >
              <div className="flex items-center gap-3">
                {m.movement_type === "in" ? (
                  <ArrowDownCircle className="h-5 w-5 text-emerald-400" />
                ) : (
                  <ArrowUpCircle className="h-5 w-5 text-red-400" />
                )}
                <div>
                  <p className="font-medium">{m.product_name}</p>
                  <p className="text-xs text-gray-500">{m.note || "—"}</p>
                </div>
              </div>
              <div className="text-right">
                <Badge
                  label={m.movement_type === "in" ? "Кіріс" : "Шығыс"}
                  variant={m.movement_type === "in" ? "income" : "expense"}
                />
                <p className="mt-1 font-mono">{m.quantity}</p>
                <p className="text-xs text-gray-400">
                  {Number(m.total_amount).toLocaleString()} ₸
                </p>
                {m.finance_entry_id && (
                  <p className="text-[11px] text-emerald-400">
                    Қаржы #{m.finance_entry_id}
                  </p>
                )}
                <p className="text-xs text-gray-500">
                  {new Date(m.created_at).toLocaleString("kk-KZ")}
                </p>
              </div>
            </div>
          ))}
          {movements.length === 0 && (
            <EmptyState
              title="Операциялар жоқ"
              description="Кіріс/шығыс операциясын жасағанда тарих осында шығады."
            />
          )}
        </div>
      )}
    </div>
  );
}
