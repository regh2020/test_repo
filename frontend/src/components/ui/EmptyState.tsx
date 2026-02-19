import type { LucideIcon } from "lucide-react";
import { cn } from "@/utils/cn";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 py-16 px-6 text-center",
        className
      )}
    >
      {Icon && <Icon className="w-10 h-10 text-slate-300" strokeWidth={1.5} />}
      <p className="text-sm font-semibold text-slate-600">{title}</p>
      {description && (
        <p className="text-sm text-slate-400 max-w-xs">{description}</p>
      )}
      {action}
    </div>
  );
}
