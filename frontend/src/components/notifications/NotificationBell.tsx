"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Bell, CheckCheck } from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";
import type { NotificationItem, PaginatedResponse } from "@/lib/types";

function formatTime(value: string) {
  return new Date(value).toLocaleString("kk-KZ", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      api.get<PaginatedResponse<NotificationItem>>("/notifications/?page_size=8"),
      api.get<{ success: boolean; count: number }>("/notifications/unread-count/"),
    ])
      .then(([list, count]) => {
        setItems(list.data.results ?? []);
        setUnread(count.data.count);
      })
      .catch(() => {
        setItems([]);
        setUnread(0);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 30000);
    return () => window.clearInterval(timer);
  }, [load]);

  async function markAllRead() {
    try {
      await api.post("/notifications/mark-all-read/");
      load();
    } catch {
      setUnread(0);
    }
  }

  async function markRead(id: number) {
    try {
      await api.post(`/notifications/${id}/mark-read/`);
      load();
    } catch {
      setItems((current) =>
        current.map((item) => (item.id === id ? { ...item, is_read: true } : item))
      );
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => {
          setOpen(!open);
          if (!open) load();
        }}
        className="relative rounded-2xl border border-white/10 bg-white/[0.06] p-2 text-gray-300 shadow-lg shadow-black/10 transition hover:border-cyan-300/40 hover:text-white"
        aria-label="Notifications"
      >
        <Bell className="h-4 w-4" />
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-gradient-to-r from-red-500 to-pink-500 px-1 text-[10px] font-bold text-white shadow-lg shadow-red-500/30">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-3 w-[360px] overflow-hidden rounded-3xl border border-white/10 bg-[#0b1020]/95 shadow-2xl shadow-black/50 backdrop-blur-2xl">
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
            <div>
              <h3 className="font-semibold">Notifications</h3>
              <p className="text-xs text-gray-500">{unread} оқылмаған</p>
            </div>
            <button
              onClick={markAllRead}
              className="inline-flex items-center gap-1 rounded-xl px-2 py-1 text-xs text-gray-400 hover:bg-white/5 hover:text-white"
            >
              <CheckCheck className="h-3 w-3" />
              бәрін оқу
            </button>
          </div>

          <div className="max-h-[420px] overflow-auto">
            {loading && items.length === 0 ? (
              <p className="p-4 text-sm text-gray-400">Жүктелуде...</p>
            ) : items.length === 0 ? (
              <p className="p-6 text-center text-sm text-gray-500">
                Хабарлама жоқ.
              </p>
            ) : (
              items.map((item) => {
                const content = (
                  <div
                    className={clsx(
                      "border-b border-white/10 px-4 py-3 transition hover:bg-white/[0.06]",
                      !item.is_read && "bg-brand-500/10"
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-medium">{item.title}</p>
                      {!item.is_read && (
                        <span className="mt-1 h-2 w-2 rounded-full bg-cyan-300 shadow-lg shadow-cyan-300/40" />
                      )}
                    </div>
                    {item.message && (
                      <p className="mt-1 line-clamp-2 text-xs text-gray-400">
                        {item.message}
                      </p>
                    )}
                    <div className="mt-2 flex items-center justify-between text-[11px] text-gray-500">
                      <span>{item.actor_name || "System"}</span>
                      <span>{formatTime(item.created_at)}</span>
                    </div>
                  </div>
                );

                if (item.link) {
                  return (
                    <Link
                      key={item.id}
                      href={item.link}
                      onClick={() => {
                        markRead(item.id);
                        setOpen(false);
                      }}
                    >
                      {content}
                    </Link>
                  );
                }

                return (
                  <button
                    key={item.id}
                    onClick={() => markRead(item.id)}
                    className="block w-full text-left"
                  >
                    {content}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
