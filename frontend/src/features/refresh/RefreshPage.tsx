import { useState } from "react";
import {
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Zap,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { useRefresh } from "./useRefresh";
import type { RefreshSourceResult } from "@/types";

export function RefreshPage() {
  const refresh = useRefresh();
  const [forceRefresh, setForceRefresh] = useState(false);

  const handleRefreshAll = () => {
    refresh.mutate({ force: forceRefresh });
  };

  const results = refresh.data?.results ?? [];

  const changed = results.filter((r) => r.changed).length;
  const failed = results.filter((r) => r.error).length;
  const unchanged = results.filter((r) => !r.changed && !r.error).length;

  return (
    <div>
      <PageHeader
        title="Refresh Status"
        description="Manually trigger source refreshes and inspect results."
      />

      <div className="max-w-3xl space-y-6">
        {/* Controls */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4 text-brand-600" />
              <CardTitle>Trigger Refresh</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-600">
              Run a refresh over all due sources. Sources are skipped if their
              content hash has not changed since the last fetch — the backend
              will only call the Anthropic AI extraction when content has
              actually changed.
            </p>

            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={forceRefresh}
                onChange={(e) => setForceRefresh(e.target.checked)}
                className="rounded"
              />
              <Zap className="h-3.5 w-3.5 text-amber-500" />
              Force refresh (ignore content hash, re-extract everything)
            </label>

            <Button
              onClick={handleRefreshAll}
              loading={refresh.isPending}
              className="w-full sm:w-auto"
            >
              <RefreshCw className="h-4 w-4" />
              {refresh.isPending ? "Refreshing…" : "Refresh All Sources"}
            </Button>

            {refresh.isError && <ErrorMessage error={refresh.error} />}
          </CardContent>
        </Card>

        {/* Summary */}
        {refresh.isSuccess && results.length > 0 && (
          <div className="grid grid-cols-3 gap-4">
            <SummaryTile
              label="Changed"
              count={changed}
              variant="success"
              icon={CheckCircle2}
            />
            <SummaryTile
              label="Unchanged"
              count={unchanged}
              variant="secondary"
              icon={RefreshCw}
            />
            <SummaryTile
              label="Errors"
              count={failed}
              variant={failed > 0 ? "destructive" : "secondary"}
              icon={XCircle}
            />
          </div>
        )}

        {/* Results list */}
        {refresh.isSuccess && results.length === 0 && (
          <EmptyState
            icon={RefreshCw}
            title="No sources refreshed"
            description="No sources were due for refresh. Try enabling force refresh."
          />
        )}

        {refresh.isSuccess && results.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Source Results</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="divide-y divide-slate-100">
                {results.map((result) => (
                  <RefreshResultRow key={result.source_id} result={result} />
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function SummaryTile({
  label,
  count,
  variant,
  icon: Icon,
}: {
  label: string;
  count: number;
  variant: React.ComponentProps<typeof Badge>["variant"];
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
      <Icon
        className={`h-6 w-6 mx-auto mb-1.5 ${
          variant === "success"
            ? "text-emerald-500"
            : variant === "destructive"
            ? "text-red-500"
            : "text-slate-400"
        }`}
      />
      <p className="text-2xl font-semibold text-slate-900">{count}</p>
      <p className="text-xs text-slate-500 mt-0.5">{label}</p>
    </div>
  );
}

function RefreshResultRow({ result }: { result: RefreshSourceResult }) {
  return (
    <li className="py-3 flex items-start justify-between gap-4">
      <div className="min-w-0">
        <code className="text-xs font-mono text-slate-600 break-all">
          {result.source_id}
        </code>
        {result.error && (
          <div className="flex items-start gap-1 mt-1 text-xs text-red-600">
            <AlertCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
            {result.error}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {result.new_record_count > 0 && (
          <Badge variant="secondary" className="text-xs">
            {result.new_record_count} field{result.new_record_count !== 1 ? "s" : ""}
          </Badge>
        )}
        {result.error ? (
          <Badge variant="destructive">Error</Badge>
        ) : result.changed ? (
          <Badge variant="success">Changed</Badge>
        ) : (
          <Badge variant="secondary">Unchanged</Badge>
        )}
      </div>
    </li>
  );
}
