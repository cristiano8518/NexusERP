"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, type AuthResponse } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    password_confirm: "",
    first_name: "",
    last_name: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/register/", form);
      const { data } = await api.post<AuthResponse>("/auth/login/", {
        username: form.username,
        password: form.password,
      });
      login(data.access, data.refresh, data.user);
      router.push("/dashboard");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { errors?: Record<string, string[]> } } })?.response?.data
          ?.errors;
      if (msg) {
        const first = Object.values(msg)[0]?.[0];
        setError(first || "Тіркелу қатесі.");
      } else {
        setError("Тіркелу мүмкін болмады.");
      }
    } finally {
      setLoading(false);
    }
  }

  const field = (name: keyof typeof form, label: string, type = "text") => (
    <div>
      <label className="mb-1 block text-sm text-gray-400">{label}</label>
      <input
        type={type}
        value={form[name]}
        onChange={(e) => setForm({ ...form, [name]: e.target.value })}
        className="premium-input"
        required={name === "username" || name === "email" || name.includes("password")}
      />
    </div>
  );

  return (
    <main className="animated-shell flex min-h-screen items-center justify-center px-4 py-8">
      <div className="premium-card w-full max-w-md p-8">
        <div className="mb-6 text-center">
          <div className="orbital-ring mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl text-lg font-bold">
            N
          </div>
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-cyan-200">
            Аккаунт ашу
          </p>
          <h1 className="mt-3 text-3xl font-black gradient-text">Тіркелу</h1>
          <p className="mt-2 text-sm text-gray-400">Жаңа қызметкер аккаунты</p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-3">
          {field("username", "Логин")}
          {field("email", "Электрондық пошта", "email")}
          {field("first_name", "Аты")}
          {field("last_name", "Тегі")}
          {field("password", "Пароль", "password")}
          {field("password_confirm", "Парольді растау", "password")}
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
            {loading ? "Күте тұрыңыз..." : "Тіркелу"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-500">
          Аккаунтыңыз бар ма?{" "}
          <Link href="/login" className="text-brand-500 hover:underline">
            Кіру
          </Link>
        </p>
      </div>
    </main>
  );
}
