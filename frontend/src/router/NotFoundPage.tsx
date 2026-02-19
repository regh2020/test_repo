import { Link } from "react-router-dom";
import { FileQuestion } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 py-24 text-center">
      <FileQuestion className="w-16 h-16 text-slate-300" />
      <h1 className="text-2xl font-semibold text-slate-800">Page not found</h1>
      <p className="text-slate-500 max-w-sm">
        The page you are looking for does not exist or has been moved.
      </p>
      <Button asChild>
        <Link to="/">Go to Dashboard</Link>
      </Button>
    </div>
  );
}
