"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, ArrowDownCircle, ArrowUpCircle } from "lucide-react";
import { api } from "@/lib/api";
import type { PaginatedResponse, Product, StockMovement } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";

export default function ProductDetailPage() {
  const params = useParams<{ id: string }>();
  const productId = params.id;
  const [product, setProduct] = useState<Product | null>(null);
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<Product>(`/warehouse/products/${productId}/`),
      api.get<PaginatedResponse<StockMovement>>("/warehouse/movements/"),
    ])
      .then(([p, m]) => {
        setProduct(p.data);
        setMovements(m.data.results.filter((item) => String(item.product) === productId));
      })
      .finally(() => setLoading(false));
  }, [productId]);

  const totals = useMemo(() => {
    return movements.reduce(
      (acc, item) => {
        if (item.movement_type === "in") {
          acc.in += Number(item.total_amount);
        } else {
          acc.out += Number(item.total_amount);
        }
        return acc;
      },
      { in: 0, out: 0 }
    );
  }, [movements]);

  if (loading) return <p className="text-gray-400">Жүктелуде...</p>;
  if (!product) return <p className="text-red-300">Тауар табылмады.</p>;

  return (
    <div>
      <Link
        href="/dashboard/warehouse"
        className="mb-4 inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white"
      >
        <ArrowLeft className="h-4 w-4" />
        Қоймаға қайту
      </Link>

      <PageHeader
        title={product.name}
        description={`${product.sku} · ${product.category_name}`}
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-4">
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400">Қалдық</p>
          <p className="mt-1 text-2xl font-bold">{product.quantity}</p>
          {product.is_low_stock && <Badge label="Low stock" variant="high" />}
        </div>
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400">Бірлік баға</p>
          <p className="mt-1 text-2xl font-bold">{Number(product.price).toLocaleString()} ₸</p>
        </div>
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400">Inventory value</p>
          <p className="mt-1 text-2xl font-bold text-brand-400">
            {Number(product.inventory_value).toLocaleString()} ₸
          </p>
        </div>
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400">Қозғалыстар</p>
          <p className="mt-1 text-2xl font-bold">{movements.length}</p>
        </div>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400">Кіріс сомасы</p>
          <p className="mt-1 text-2xl font-bold text-emerald-400">
            {totals.in.toLocaleString()} ₸
          </p>
        </div>
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400">Шығыс сомасы</p>
          <p className="mt-1 text-2xl font-bold text-red-400">
            {totals.out.toLocaleString()} ₸
          </p>
        </div>
      </div>

      <section className="glass-card overflow-hidden">
        <div className="border-b border-surface-border px-4 py-3">
          <h3 className="font-semibold">Movement history</h3>
        </div>
        <div className="divide-y divide-surface-border">
          {movements.map((movement) => (
            <div key={movement.id} className="flex items-center justify-between gap-4 p-4 text-sm">
              <div className="flex items-center gap-3">
                {movement.movement_type === "in" ? (
                  <ArrowDownCircle className="h-5 w-5 text-emerald-400" />
                ) : (
                  <ArrowUpCircle className="h-5 w-5 text-red-400" />
                )}
                <div>
                  <p className="font-medium">
                    {movement.movement_type === "in" ? "Кіріс" : "Шығыс"} · {movement.quantity}
                  </p>
                  <p className="text-xs text-gray-500">{movement.note || "—"}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-medium">{Number(movement.total_amount).toLocaleString()} ₸</p>
                {movement.finance_entry_id && (
                  <p className="text-xs text-emerald-400">Finance #{movement.finance_entry_id}</p>
                )}
                <p className="text-xs text-gray-500">
                  {new Date(movement.created_at).toLocaleString("kk-KZ")}
                </p>
              </div>
            </div>
          ))}
          {movements.length === 0 && (
            <p className="p-6 text-center text-sm text-gray-500">Қозғалыстар жоқ.</p>
          )}
        </div>
      </section>
    </div>
  );
}
