import { cn } from "@/utils/cn";
import { formatConfidence } from "@/utils/format";

interface ConfidenceBarProps {
  value: number; // 0.0 – 1.0
  className?: string;
  showLabel?: boolean;
}

function colorClass(value: number): string {
  if (value >= 0.8) return "bg-emerald-500";
  if (value >= 0.5) return "bg-amber-400";
  return "bg-red-400";
}

export function ConfidenceBar({
  value,
  className,
  showLabel = true,
}: ConfidenceBarProps) {
  const pct = Math.round(value * 100);
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div
        className="flex-1 h-1.5 rounded-full bg-slate-200 overflow-hidden"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={cn("h-full rounded-full transition-all", colorClass(value))}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs tabular-nums text-slate-500 w-8 text-right">
          {formatConfidence(value)}
        </span>
      )}
    </div>
  );
}
