import { useRouteError, isRouteErrorResponse, Link } from "react-router-dom";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function ErrorBoundaryPage() {
  const error = useRouteError();

  const message = isRouteErrorResponse(error)
    ? `${error.status} — ${error.statusText}`
    : error instanceof Error
    ? error.message
    : "An unexpected error occurred.";

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4 p-8 text-center bg-white">
      <AlertTriangle className="w-14 h-14 text-red-400" />
      <h1 className="text-2xl font-semibold text-slate-800">
        Something went wrong
      </h1>
      <p className="text-slate-500 max-w-md font-mono text-sm bg-slate-50 border border-slate-200 rounded-md p-3">
        {message}
      </p>
      <div className="flex gap-3">
        <Button variant="outline" onClick={() => window.location.reload()}>
          Reload
        </Button>
        <Button asChild>
          <Link to="/">Go to Dashboard</Link>
        </Button>
      </div>
    </div>
  );
}
