import { Link } from "react-router-dom";
import {
  Download,
  Trash2,
  ExternalLink,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { SpinnerPage } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { Badge } from "@/components/ui/Badge";
import { ConfidenceBar } from "@/components/ui/ConfidenceBar";
import { ROUTES } from "@/router/routes";
import { displayUrl, truncate } from "@/utils/format";
import { timeAgo } from "@/utils/date";
import {
  usePendingDiscoveries,
  useImportPending,
  useDeletePending,
} from "./useDiscovery";
import type { PendingDiscovery } from "@/types";
import { useState } from "react";

export function PendingDiscoveriesPage() {
  const { data, isPending, isError, error } = usePendingDiscoveries();

  return (
    <div>
      <PageHeader
        title="Pending Discoveries"
        description="Conferences discovered but not yet imported. Click Import to run AI extraction and add to your database."
        actions={
          <Button variant="outline" size="sm" asChild>
            <Link to={ROUTES.discovery}>Search More</Link>
          </Button>
        }
      />

      {isPending && <SpinnerPage />}
      {isError && <ErrorMessage error={error} />}

      {data && data.length === 0 && (
        <EmptyState
          icon={Clock}
          title="No pending discoveries"
          description="Run a discovery search and save candidates here for review."
        />
      )}

      {data && data.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-slate-500">
            {data.length} pending candidate{data.length !== 1 ? "s" : ""}
          </p>
          {data.map((pd) => (
            <PendingCard key={pd.id} pending={pd} />
          ))}
        </div>
      )}
    </div>
  );
}

function PendingCard({ pending }: { pending: PendingDiscovery }) {
  const [importState, setImportState] = useState<
    "idle" | "importing" | "done" | "error"
  >("idle");
  const [importedId, setImportedId] = useState<string | null>(null);

  const importPending = useImportPending();
  const deletePending = useDeletePending();

  const handleImport = async () => {
    setImportState("importing");
    try {
      const result = await importPending.mutateAsync(pending.id);
      setImportedId(result.conference_id);
      setImportState("done");
    } catch {
      setImportState("error");
    }
  };

  const statusColors: Record<PendingDiscovery["status"], string> = {
    pending: "text-amber-600",
    importing: "text-blue-600",
    imported: "text-emerald-600",
    failed: "text-red-600",
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            {pending.title && (
              <p className="font-medium text-slate-900 text-sm">
                {pending.title}
              </p>
            )}
            <Badge variant="outline" className="text-xs capitalize">
              {pending.source_type}
            </Badge>
            <span className={`text-xs font-medium ${statusColors[pending.status]}`}>
              {pending.status}
            </span>
          </div>

          <a
            href={pending.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-brand-600 hover:underline flex items-center gap-1 mb-2"
          >
            {displayUrl(pending.url)}
            <ExternalLink className="h-3 w-3 shrink-0" />
          </a>

          {pending.snippet && (
            <p className="text-xs text-slate-500 leading-relaxed">
              {truncate(pending.snippet, 200)}
            </p>
          )}

          <div className="mt-2 flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Score</span>
              <ConfidenceBar value={pending.score} className="w-28" />
            </div>
            <span className="text-xs text-slate-400">
              Added {timeAgo(pending.created_at)}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-2 shrink-0">
          {importState === "idle" && pending.status !== "imported" && (
            <Button size="sm" onClick={handleImport}>
              <Download className="h-3.5 w-3.5" />
              Import
            </Button>
          )}

          {importState === "importing" && (
            <Button size="sm" disabled>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Importing…
            </Button>
          )}

          {(importState === "done" || pending.status === "imported") && (
            <div className="flex flex-col gap-1 items-end">
              <div className="flex items-center gap-1 text-emerald-600 text-xs">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Imported
              </div>
              {importedId && (
                <Button variant="ghost" size="sm" asChild>
                  <Link to={ROUTES.conferenceDetail(importedId)}>View →</Link>
                </Button>
              )}
            </div>
          )}

          {importState === "error" && (
            <div className="flex flex-col gap-1 items-end">
              <div className="flex items-center gap-1 text-red-500 text-xs">
                <XCircle className="h-3.5 w-3.5" />
                Failed
              </div>
              <Button size="sm" variant="outline" onClick={handleImport}>
                Retry
              </Button>
            </div>
          )}

          <Button
            size="sm"
            variant="ghost"
            className="text-slate-400 hover:text-red-500"
            loading={deletePending.isPending}
            onClick={() => deletePending.mutate(pending.id)}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
