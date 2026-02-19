import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Search,
  PlusCircle,
  Trash2,
  ExternalLink,
  Download,
  XCircle,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { FormField } from "@/components/ui/FormField";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { Badge } from "@/components/ui/Badge";
import { ConfidenceBar } from "@/components/ui/ConfidenceBar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { ROUTES } from "@/router/routes";
import { truncate, displayUrl } from "@/utils/format";
import { useDiscover, useImportCandidate } from "./useDiscovery";
import type { DiscoveryCandidate } from "@/types";

const schema = z.object({
  keywordsRaw: z.string().optional(),
  topicsRaw: z.string().optional(),
  date_range_start: z.string().optional(),
  date_range_end: z.string().optional(),
  include_twitter: z.boolean().default(false),
});

type FormValues = z.infer<typeof schema>;

function parseTokens(raw: string | undefined): string[] {
  return (raw ?? "")
    .split(/[\s,]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export function DiscoveryPage() {
  const discover = useDiscover();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { include_twitter: false },
  });

  const onSubmit = (values: FormValues) => {
    discover.mutate({
      keywords: parseTokens(values.keywordsRaw),
      topics: parseTokens(values.topicsRaw),
      date_range_start: values.date_range_start || null,
      date_range_end: values.date_range_end || null,
      include_twitter: values.include_twitter,
    });
  };

  const candidates = discover.data?.candidates ?? [];

  return (
    <div>
      <PageHeader
        title="Discover Conferences"
        description="Search the web for new conference announcements and import them."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Search form */}
        <Card className="lg:col-span-1 self-start">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Search className="h-4 w-4 text-brand-600" />
              <CardTitle>Search Parameters</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                label="Keywords"
                error={errors.keywordsRaw?.message}
                hint="Space or comma separated"
              >
                <Input
                  {...register("keywordsRaw")}
                  placeholder="machine learning, NLP"
                />
              </FormField>

              <FormField
                label="Topics"
                error={errors.topicsRaw?.message}
                hint="Space or comma separated"
              >
                <Input {...register("topicsRaw")} placeholder="AI, vision" />
              </FormField>

              <div className="grid grid-cols-2 gap-2">
                <FormField
                  label="From"
                  error={errors.date_range_start?.message}
                >
                  <Input type="date" {...register("date_range_start")} />
                </FormField>
                <FormField label="To" error={errors.date_range_end?.message}>
                  <Input type="date" {...register("date_range_end")} />
                </FormField>
              </div>

              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  {...register("include_twitter")}
                  className="rounded"
                />
                Include Twitter / X
              </label>

              <Button
                type="submit"
                className="w-full"
                loading={discover.isPending}
              >
                <Search className="h-4 w-4" />
                {discover.isPending ? "Searching…" : "Search"}
              </Button>

              {discover.isError && (
                <ErrorMessage error={discover.error} />
              )}
            </form>
          </CardContent>
        </Card>

        {/* Results */}
        <div className="lg:col-span-2">
          {!discover.isSuccess && !discover.isPending && (
            <EmptyState
              icon={Search}
              title="Enter search parameters"
              description="Results will appear here once you run a discovery search."
            />
          )}

          {discover.isPending && (
            <div className="flex flex-col items-center justify-center gap-3 py-24 text-slate-500">
              <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
              <p className="text-sm">Searching the web…</p>
            </div>
          )}

          {discover.isSuccess && candidates.length === 0 && (
            <EmptyState
              icon={Search}
              title="No candidates found"
              description="Try broader keywords or different topics."
            />
          )}

          {discover.isSuccess && candidates.length > 0 && (
            <div className="space-y-3">
              <p className="text-sm text-slate-500">
                {candidates.length} candidate
                {candidates.length !== 1 ? "s" : ""} found
              </p>
              {candidates.map((candidate, i) => (
                <CandidateCard key={`${candidate.url}-${i}`} candidate={candidate} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Candidate card ───────────────────────────────────────────────────────────

type ImportState = "idle" | "importing" | "done" | "error";

function CandidateCard({ candidate }: { candidate: DiscoveryCandidate }) {
  const [importState, setImportState] = useState<ImportState>("idle");
  const [importedId, setImportedId] = useState<string | null>(null);

  const importCandidate = useImportCandidate();

  const handleImport = async () => {
    setImportState("importing");
    try {
      const result = await importCandidate.mutateAsync(candidate.url);
      setImportedId(result.conference_id);
      setImportState("done");
    } catch {
      setImportState("error");
    }
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 hover:border-slate-300 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            {candidate.title && (
              <p className="font-medium text-slate-900 text-sm">
                {candidate.title}
              </p>
            )}
            <Badge variant="outline" className="text-xs capitalize">
              {candidate.source_type}
            </Badge>
          </div>

          <a
            href={candidate.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-brand-600 hover:underline flex items-center gap-1 mb-2"
          >
            {displayUrl(candidate.url)}
            <ExternalLink className="h-3 w-3 shrink-0" />
          </a>

          {candidate.snippet && (
            <p className="text-xs text-slate-500 leading-relaxed">
              {truncate(candidate.snippet, 200)}
            </p>
          )}

          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs text-slate-400">Score</span>
            <ConfidenceBar value={candidate.score} className="w-28" />
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-2 shrink-0">
          {importState === "idle" && (
            <Button size="sm" onClick={handleImport}>
              <Download className="h-3.5 w-3.5" />
              Import
            </Button>
          )}

          {importState === "importing" && (
            <Button size="sm" loading>
              Importing
            </Button>
          )}

          {importState === "done" && (
            <div className="flex flex-col gap-1 items-end">
              <div className="flex items-center gap-1 text-emerald-600 text-xs">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Imported
              </div>
              {importedId && (
                <Button variant="ghost" size="sm" asChild>
                  <Link to={ROUTES.conferenceDetail(importedId)}>
                    View <ArrowRight className="h-3 w-3" />
                  </Link>
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
        </div>
      </div>
    </div>
  );
}

// Fix missing import
function ArrowRight({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  );
}
