import Link from "next/link";
import { ArrowRight, BarChart3, Shield, Users } from "lucide-react";

export default function HomePage() {
  return (
    <main className="animated-shell min-h-screen">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-6 py-10">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="orbital-ring flex h-11 w-11 items-center justify-center rounded-2xl font-bold text-white shadow-lg shadow-brand-900/30">
              N
            </div>
            <span className="text-xl font-semibold tracking-tight text-white">NexusERP</span>
          </div>
          <div className="flex gap-3">
            <Link
              href="/login"
              className="rounded-2xl px-4 py-2 text-sm text-gray-300 transition hover:bg-white/5 hover:text-white"
            >
              Кіру
            </Link>
            <Link
              href="/login"
              className="rounded-2xl bg-white px-4 py-2 text-sm font-semibold text-slate-950 shadow-lg shadow-white/10 transition hover:-translate-y-0.5"
            >
              Бастау
            </Link>
          </div>
        </header>

        <section className="grid flex-1 items-center gap-12 py-16 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <div className="mb-5 inline-flex rounded-full border border-white/10 bg-white/[0.06] px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-cyan-200 shadow-lg shadow-cyan-950/20 backdrop-blur-xl">
              Enterprise ERP Platform
            </div>
            <h1 className="max-w-4xl text-5xl font-black leading-[0.95] tracking-tight md:text-7xl">
              Компанияны{" "}
              <span className="gradient-text">бір жүйеден</span>{" "}
              басқару
            </h1>
            <p className="mt-7 max-w-2xl text-lg leading-8 text-gray-300">
              Қызметкерлер, тапсырмалар, қойма, қаржы, аналитика және есептер —
              барлығы бір premium корпоративтік платформаның ішінде.
            </p>
            <div className="mt-10 flex flex-wrap gap-4">
              <Link href="/dashboard" className="premium-button">
                Dashboard
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="http://localhost:8000/api/docs/"
                target="_blank"
                rel="noopener noreferrer"
                className="ghost-button"
              >
                API Docs
              </a>
            </div>
          </div>

          <div className="relative">
            <div className="absolute -inset-6 rounded-[2.5rem] bg-gradient-to-r from-brand-500/20 via-purple-500/20 to-cyan-500/20 blur-2xl" />
            <div className="premium-card relative overflow-hidden p-6">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Live business overview</p>
                  <h2 className="mt-1 text-2xl font-bold">Nexus Control Center</h2>
                </div>
                <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-medium text-emerald-300">
                  Online
                </span>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  ["HR", "128", "employees"],
                  ["Tasks", "86%", "completed"],
                  ["Stock", "2.4K", "items"],
                  ["Finance", "+18%", "growth"],
                ].map(([label, value, desc]) => (
                  <div key={label} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                    <p className="text-xs uppercase tracking-widest text-gray-500">{label}</p>
                    <p className="mt-3 text-3xl font-black">{value}</p>
                    <p className="mt-1 text-sm text-gray-400">{desc}</p>
                  </div>
                ))}
              </div>
              <div className="mt-5 h-3 overflow-hidden rounded-full bg-white/5">
                <div className="h-full w-4/5 rounded-full bg-gradient-to-r from-brand-500 via-purple-500 to-cyan-400" />
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-6 pb-8 md:grid-cols-3">
          {[
            { icon: Users, title: "HR & Қызметкерлер", desc: "Бөлімдер, лауазымдар, профильдер" },
            { icon: BarChart3, title: "Аналитика", desc: "KPI, графиктер, real-time dashboard" },
            { icon: Shield, title: "Қауіпсіздік", desc: "JWT, рөлдер, audit логтары" },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="premium-card p-6">
              <Icon className="mb-5 h-9 w-9 text-cyan-300" />
              <h3 className="font-semibold">{title}</h3>
              <p className="mt-2 text-sm text-gray-400">{desc}</p>
            </div>
          ))}
        </section>
      </div>
    </main>
  );
}
