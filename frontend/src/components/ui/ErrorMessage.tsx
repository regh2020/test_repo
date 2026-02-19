import { AlertCircle } from "lucide-react";
import { cn } from "@/utils/cn";
import type { ApiError } from "@/types";

interface ErrorMessageProps {
  error: ApiError | Error | unknown;
  className?: string;
  title?: string;
}

function extractMessage(error: unknown): string {
  if (!error) return "An error occurred.";
  if (typeof error === "object" && error !== null && "detail" in error) {
    return (error as ApiError).detail;
  }
  if (error instanceof Error) return error.message;
  return String(error);
}

export function ErrorMessage({
  error,
  className,
  title = "Something went wrong",
}: ErrorMessageProps) {
  return (
    <div
      className={cn(
        "flex gap-3 items-start rounded-md border border-red-200 bg-red-50 p-4 text-sm",
        className
      )}
    >
      <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
      <div>
        <p className="font-medium text-red-800">{title}</p>
        <p className="text-red-600 mt-0.5">{extractMessage(error)}</p>
      </div>
    </div>
  );
}
