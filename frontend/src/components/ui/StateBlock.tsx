import type { ReactNode } from "react";
import { Loader2 } from "lucide-react";

export function LoadingState({ label = "Жүктелуде..." }: { label?: string }) {
  return (
    <div className="glass-card flex items-center justify-center gap-3 p-8 text-sm text-gray-400">
      <Loader2 className="h-4 w-4 animate-spin" />
      {label}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="glass-card p-8 text-center">
      <p className="font-medium text-gray-200">{title}</p>
      {description && <p className="mx-auto mt-2 max-w-md text-sm text-gray-500">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
