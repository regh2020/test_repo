import { cn } from "@/utils/cn";

interface SpinnerProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

const sizes = {
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-10 w-10 border-[3px]",
};

export function Spinner({ className, size = "md" }: SpinnerProps) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cn(
        "inline-block animate-spin rounded-full border-slate-200 border-t-brand-600",
        sizes[size],
        className
      )}
    />
  );
}

export function SpinnerPage() {
  return (
    <div className="flex items-center justify-center h-64 w-full">
      <Spinner size="lg" />
    </div>
  );
}
