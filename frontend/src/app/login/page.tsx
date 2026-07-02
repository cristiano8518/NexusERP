"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, type AuthResponse } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await api.post<AuthResponse>("/auth/login/", { username, password });
      login(data.access, data.refresh, data.user);
      router.push("/dashboard");
    } catch (err: unknown) {
      const ax = err as { response?: { status?: number }; message?: string };
      if (!ax.response) {
        setError(
          "Серверге қосылмады. Docker іске қосылғанын тексеріңіз: localhost:8000/api/v1/health/"
        );
      } else if (ax.response.status === 401) {
        setError("Логин немесе пароль қате. Терминалда: docker compose exec backend python manage.py reset_demo_passwords");
      } else {
        setError(`Қате (${ax.response.status}). Backend логтарын тексеріңіз.`);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="animated-shell flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <Link href="/" className="inline-flex items-center gap-3 text-gray-300 hover:text-white">
            <span className="orbital-ring flex h-11 w-11 items-center justify-center rounded-2xl font-bold">
              N
            </span>
            <span className="font-semibold">NexusERP</span>
          </Link>
        </div>
      <div className="premium-card p-8">
        <div className="mb-8 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-cyan-200">
            Қайта қош келдіңіз
          </p>
          <h1 className="mt-3 text-3xl font-black gradient-text">Жүйеге кіру</h1>
          <p className="mt-2 text-sm text-gray-400">ERP басқару панеліне өтіңіз</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm text-gray-400">Логин</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="premium-input"
              placeholder="admin"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-gray-400">Пароль</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="premium-input"
              placeholder="••••••••"
              required
            />
          </div>
          {error && (
            <p className="rounded-2xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="premium-button w-full"
          >
            {loading ? "Күте тұрыңыз..." : "Кіру"}
          </button>
        </form>

        <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.04] p-4 text-xs text-gray-400">
          Демо: <span className="text-gray-200">admin / admin123</span>, менеджер және қызметкер аккаунттарын seed командасы арқылы қосуға болады.
        </div>

        <p className="mt-6 text-center text-sm text-gray-500">
          Аккаунт жоқ па?{" "}
          <Link href="/register" className="text-brand-500 hover:underline">
            Тіркелу
          </Link>
          {" · "}
          <Link href="/" className="text-gray-500 hover:underline">
            Басты бет
          </Link>
        </p>
      </div>
      </div>
    </main>
  );
}
