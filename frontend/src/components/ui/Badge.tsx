import clsx from "clsx";

const variants: Record<string, string> = {
  admin: "border-purple-400/20 bg-purple-500/15 text-purple-200",
  manager: "border-blue-400/20 bg-blue-500/15 text-blue-200",
  employee: "border-emerald-400/20 bg-emerald-500/15 text-emerald-200",
  draft: "border-gray-400/20 bg-gray-500/15 text-gray-300",
  assigned: "border-amber-400/20 bg-amber-500/15 text-amber-200",
  in_progress: "border-blue-400/20 bg-blue-500/15 text-blue-200",
  done: "border-emerald-400/20 bg-emerald-500/15 text-emerald-200",
  approved: "border-green-400/20 bg-green-500/15 text-green-200",
  rejected: "border-red-400/20 bg-red-500/15 text-red-200",
  low: "border-gray-400/20 bg-gray-500/15 text-gray-300",
  medium: "border-amber-400/20 bg-amber-500/15 text-amber-200",
  high: "border-red-400/20 bg-red-500/15 text-red-200",
  income: "border-emerald-400/20 bg-emerald-500/15 text-emerald-200",
  expense: "border-red-400/20 bg-red-500/15 text-red-200",
};

export function Badge({ label, variant }: { label: string; variant: string }) {
  return (
    <span
      className={clsx(
        "inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold shadow-sm backdrop-blur-xl",
        variants[variant] ?? "border-gray-400/20 bg-gray-500/15 text-gray-300"
      )}
    >
      {label}
    </span>
  );
}
