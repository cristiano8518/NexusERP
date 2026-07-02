"use client";

import { FormEvent, useState } from "react";
import { Bot, Send, Sparkles, UserRound } from "lucide-react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { useAuth } from "@/contexts/AuthContext";
import { ROLE_LABELS } from "@/lib/auth";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

const quickPrompts = [
  "ERP жағдайын 1 сөйлеммен айт",
  "Басты тәуекелді 1 сөйлеммен айт",
  "Қаржы балансын 1 сөйлеммен айт",
  "Қойма бойынша 1 кеңес бер",
];

export default function AiAssistantPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Сәлем! Мен NexusERP AI көмекшісімін. ERP деректері бойынша қазақша түсіндірме, қысқаша қорытынды және ұсыныс бере аламын.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function sendMessage(e?: FormEvent, preset?: string) {
    e?.preventDefault();
    const message = (preset || input).trim();
    if (!message || loading) return;

    setError("");
    setInput("");
    setMessages((current) => [...current, { role: "user", content: message }]);
    setLoading(true);

    try {
      const { data } = await api.post<{ success: boolean; answer?: string; detail?: string }>("/ai/chat/", {
        message,
      });
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            data.answer ||
            data.detail ||
            "Жауап бос келді. Ollama модель параметрін тексеріңіз.",
        },
      ]);
    } catch (err: unknown) {
      const hasResponse = Boolean((err as { response?: unknown })?.response);
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (hasResponse
          ? "AI көмекшіге қосылу мүмкін болмады. Ollama іске қосылғанын тексеріңіз."
          : "Backend жауап бермеді. Ollama бірінші жүктелуі ұзақ болуы мүмкін, backend қайта қосылғанын тексеріңіз.");
      setError(detail);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: detail,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="AI көмекші"
        description="Ollama арқылы NexusERP деректерін қазақша түсіндіретін локалды көмекші"
      />

      <section className="grid gap-6 xl:grid-cols-[1.4fr_0.6fr]">
        <div className="premium-card flex min-h-[620px] flex-col overflow-hidden">
          <div className="border-b border-white/10 px-5 py-4">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-brand-500/15 p-3">
                <Bot className="h-5 w-5 text-brand-300" />
              </div>
              <div>
                <h2 className="font-semibold">NexusERP көмекшісі</h2>
                <p className="text-sm text-gray-400">
                  Рөл: {user ? ROLE_LABELS[user.role] : "—"} · жауаптар ERP қамту аясы бойынша шектеледі
                </p>
              </div>
            </div>
          </div>

          <div className="flex-1 space-y-4 overflow-auto p-5">
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {message.role === "assistant" && (
                  <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-brand-500/15">
                    <Bot className="h-4 w-4 text-brand-300" />
                  </div>
                )}
                <div
                  className={`max-w-[85%] whitespace-pre-wrap rounded-3xl px-4 py-3 text-sm leading-6 ${
                    message.role === "user"
                      ? "bg-brand-600 text-white"
                      : "border border-white/10 bg-white/5 text-gray-100"
                  }`}
                >
                  {message.content}
                </div>
                {message.role === "user" && (
                  <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-white/10">
                    <UserRound className="h-4 w-4 text-gray-200" />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-3 text-sm text-gray-400">
                <Sparkles className="h-4 w-4 animate-pulse text-brand-300" />
                Ollama жауап дайындап жатыр...
              </div>
            )}
          </div>

          {error && (
            <p className="mx-5 mb-3 rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </p>
          )}

          <form onSubmit={(e) => sendMessage(e)} className="border-t border-white/10 p-4">
            <div className="flex gap-3">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Мысалы: Осы аптадағы тапсырмалар жағдайын түсіндір..."
                className="premium-input flex-1"
                disabled={loading}
              />
              <button type="submit" className="premium-button px-4 py-2" disabled={loading}>
                <Send className="h-4 w-4" />
                Жіберу
              </button>
            </div>
          </form>
        </div>

        <aside className="space-y-4">
          <div className="premium-card p-5">
            <h3 className="mb-3 font-semibold">Жылдам сұрақтар</h3>
            <div className="space-y-2">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => sendMessage(undefined, prompt)}
                  className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-left text-sm text-gray-300 transition hover:border-brand-400/40 hover:text-white"
                  disabled={loading}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          <div className="premium-card p-5 text-sm text-gray-400">
            <h3 className="mb-2 font-semibold text-white">Қалай жұмыс істейді?</h3>
            <p>
              Сұрақ Django backend-ке жіберіледі. Backend рөліңізге сай ERP контекст жинап,
              локалды Ollama моделіне береді. Құпия token немесе пароль сұрауға қосылмайды.
            </p>
          </div>
        </aside>
      </section>
    </div>
  );
}
