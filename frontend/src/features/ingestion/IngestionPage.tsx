import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Link2,
  CheckCircle2,
  XCircle,
  ArrowRight,
  AlertTriangle,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { FormField } from "@/components/ui/FormField";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ROUTES } from "@/router";
import { useIngestUrl } from "./useIngestion";
import type { IngestResponse } from "@/types";

const schema = z.object({
  url: z.string().url("Please enter a valid URL (include https://)"),
  attach_to_conference_id: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export function IngestionPage() {
  const [result, setResult] = useState<IngestResponse | null>(null);

  const ingest = useIngestUrl();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setResult(null);
    const res = await ingest.mutateAsync({
      url: values.url,
      attach_to_conference_id: values.attach_to_conference_id || null,
    });
    setResult(res);
  };

  const handleReset = () => {
    reset();
    setResult(null);
    ingest.reset();
  };

  return (
    <div>
      <PageHeader
        title="Ingest URL"
        description="Paste a conference or CFP URL. The system will fetch, extract, and store structured data."
      />

      <div className="max-w-2xl space-y-6">
        {/* Input form */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Link2 className="h-4 w-4 text-brand-600" />
              <CardTitle>Conference URL</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {ingest.isError && (
              <ErrorMessage error={ingest.error} className="mb-4" />
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                label="URL to ingest"
                required
                error={errors.url?.message}
                hint="Supports conference websites, CFP pages, and more."
              >
                <Input
                  {...register("url")}
                  type="url"
                  placeholder="https://icml.cc/2025"
                  error={Boolean(errors.url)}
                  className="font-mono text-sm"
                />
              </FormField>

              <FormField
                label="Attach to existing conference (optional)"
                error={errors.attach_to_conference_id?.message}
                hint="Conference ID — leave blank to create a new record automatically."
              >
                <Input
                  {...register("attach_to_conference_id")}
                  placeholder="Conference ID (optional)"
                />
              </FormField>

              <div className="flex gap-3 pt-1">
                <Button
                  type="submit"
                  loading={ingest.isPending}
                  disabled={Boolean(result && !ingest.isError)}
                >
                  {ingest.isPending ? "Ingesting…" : "Ingest URL"}
                </Button>
                {(result || ingest.isError) && (
                  <Button type="button" variant="outline" onClick={handleReset}>
                    Try Another URL
                  </Button>
                )}
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Result preview */}
        {result && <IngestionResultCard result={result} />}
      </div>
    </div>
  );
}

// ─── Result card ──────────────────────────────────────────────────────────────

function IngestionResultCard({ result }: { result: IngestResponse }) {
  const success = !result.error;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          {success ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
          ) : (
            <XCircle className="h-5 w-5 text-red-500" />
          )}
          <CardTitle>{success ? "Ingestion Complete" : "Ingestion Failed"}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {result.error && (
          <div className="flex items-start gap-2 mb-4 p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-700">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            {result.error}
          </div>
        )}

        <dl className="space-y-3 text-sm">
          <ResultRow
            label="Conference"
            value={
              result.conference_id ? (
                <Link
                  to={ROUTES.conferenceDetail(result.conference_id)}
                  className="text-brand-600 hover:underline flex items-center gap-1"
                >
                  View conference
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              ) : (
                <span className="text-slate-400">Not created</span>
              )
            }
          />
          <ResultRow
            label="Source ID"
            value={
              <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded font-mono">
                {result.source_id}
              </code>
            }
          />
          <ResultRow
            label="Extracted fields"
            value={
              <Badge variant={result.extraction_count > 0 ? "success" : "secondary"}>
                {result.extraction_count} field
                {result.extraction_count !== 1 ? "s" : ""}
              </Badge>
            }
          />
        </dl>

        {result.conference_id && (
          <div className="mt-5 pt-4 border-t border-slate-100 flex gap-3">
            <Button asChild size="sm">
              <Link to={ROUTES.conferenceDetail(result.conference_id)}>
                View Conference
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link
                to={ROUTES.conferenceEdit(result.conference_id)}
              >
                Edit Details
              </Link>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ResultRow({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <dt className="text-slate-500 shrink-0">{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
