import { useParams, Link, useNavigate } from "react-router-dom";
import {
  Edit2,
  ExternalLink,
  RefreshCw,
  PlusCircle,
  Trash2,
  MapPin,
  Calendar,
  Globe,
  Tag,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { SpinnerPage } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { ConfidenceBar } from "@/components/ui/ConfidenceBar";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { ROUTES } from "@/router/routes";
import { formatDate, formatDateRange, timeAgo } from "@/utils/date";
import { formatImportantDateType, displayUrl } from "@/utils/format";
import {
  useConference,
  useConferenceDates,
  useConferenceSources,
  useDeleteConference,
  useDeleteDate,
} from "./useConferences";
import { AddSourceDialog } from "./AddSourceDialog";
import { AddDateDialog } from "./AddDateDialog";
import { RefreshConferenceButton } from "../refresh/RefreshConferenceButton";

export function ConferenceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: conf, isPending, isError, error } = useConference(id!);
  const { data: dates = [] } = useConferenceDates(id!);
  const { data: sources = [] } = useConferenceSources(id!);

  const deleteConference = useDeleteConference();

  const handleDelete = async () => {
    if (!conf) return;
    const ok = window.confirm(
      `Delete "${conf.name}"? This action cannot be undone.`
    );
    if (!ok) return;
    await deleteConference.mutateAsync(conf.id);
    navigate(ROUTES.conferences);
  };

  if (isPending) return <SpinnerPage />;
  if (isError) return <ErrorMessage error={error} className="mt-8" />;
  if (!conf) return null;

  return (
    <div>
      <PageHeader
        title={conf.acronym ? `${conf.acronym} — ${conf.name}` : conf.name}
        description={`Created ${timeAgo(conf.created_at)} · Updated ${timeAgo(conf.updated_at)}`}
        actions={
          <div className="flex gap-2">
            <RefreshConferenceButton conferenceId={conf.id} />
            <Button variant="outline" size="sm" asChild>
              <Link to={ROUTES.conferenceEdit(conf.id)}>
                <Edit2 className="h-3.5 w-3.5" />
                Edit
              </Link>
            </Button>
            <Button
              variant="destructive"
              size="sm"
              loading={deleteConference.isPending}
              onClick={handleDelete}
            >
              <Trash2 className="h-3.5 w-3.5" />
              Delete
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: main info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Overview card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Overview</CardTitle>
                <StatusBadge status={conf.status} />
              </div>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4 text-sm">
                <InfoRow
                  icon={Calendar}
                  label="Dates"
                  value={formatDateRange(conf.start_date, conf.end_date)}
                />
                <InfoRow
                  icon={MapPin}
                  label="Location"
                  value={
                    conf.is_online
                      ? "Online"
                      : [conf.venue, conf.city, conf.country]
                          .filter(Boolean)
                          .join(", ") || "—"
                  }
                />
                {conf.website_url && (
                  <InfoRow
                    icon={Globe}
                    label="Website"
                    value={
                      <a
                        href={conf.website_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-brand-600 hover:underline flex items-center gap-1"
                      >
                        {displayUrl(conf.website_url)}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    }
                  />
                )}
                {conf.cfp_url && (
                  <InfoRow
                    icon={ExternalLink}
                    label="CFP"
                    value={
                      <a
                        href={conf.cfp_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-brand-600 hover:underline flex items-center gap-1"
                      >
                        {displayUrl(conf.cfp_url)}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    }
                  />
                )}
                {conf.series && (
                  <InfoRow icon={Tag} label="Series" value={conf.series} />
                )}
                {conf.is_hybrid && (
                  <div className="sm:col-span-2">
                    <Badge variant="secondary">Hybrid</Badge>
                  </div>
                )}
              </dl>

              {conf.topics.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-100">
                  <p className="text-xs font-medium text-slate-500 mb-2">
                    Topics
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {conf.topics.map((t) => (
                      <Badge key={t} variant="default">
                        {t}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Important dates */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Important Dates</CardTitle>
                <AddDateDialog conferenceId={conf.id} />
              </div>
            </CardHeader>
            <CardContent>
              {dates.length === 0 ? (
                <EmptyState
                  icon={Calendar}
                  title="No important dates"
                  description="Add submission deadlines, notifications, and more."
                />
              ) : (
                <ImportantDateTable conferenceId={conf.id} dates={dates} />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right column: sources */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Sources</CardTitle>
                <AddSourceDialog conferenceId={conf.id} />
              </div>
            </CardHeader>
            <CardContent>
              {sources.length === 0 ? (
                <EmptyState
                  icon={Globe}
                  title="No sources"
                  description="Link websites or CFP pages to track updates."
                />
              ) : (
                <ul className="space-y-3">
                  {sources.map((src) => (
                    <li
                      key={src.id}
                      className="text-sm border border-slate-100 rounded-md p-3"
                    >
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <Badge variant="outline" className="uppercase text-xs">
                          {src.type}
                        </Badge>
                        <span
                          className={
                            src.fetch_status === "ok"
                              ? "text-emerald-600 text-xs"
                              : "text-amber-600 text-xs"
                          }
                        >
                          {src.fetch_status ?? "—"}
                        </span>
                      </div>
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-brand-600 hover:underline break-all"
                      >
                        {displayUrl(src.url)}
                      </a>
                      <p className="text-xs text-slate-400 mt-1">
                        Last fetched:{" "}
                        {src.last_fetched_at
                          ? timeAgo(src.last_fetched_at)
                          : "Never"}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-2">
      <Icon className="h-3.5 w-3.5 text-slate-400 mt-0.5 shrink-0" />
      <div>
        <dt className="text-xs text-slate-400">{label}</dt>
        <dd className="text-slate-800 font-medium">{value}</dd>
      </div>
    </div>
  );
}

function ImportantDateTable({
  conferenceId,
  dates,
}: {
  conferenceId: string;
  dates: Array<{
    id: string;
    type: string;
    date_time: string;
    timezone: string | null;
    note: string | null;
  }>;
}) {
  const deleteDate = useDeleteDate(conferenceId);

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-slate-100">
          <th className="pb-2 text-left text-xs font-medium text-slate-500">
            Type
          </th>
          <th className="pb-2 text-left text-xs font-medium text-slate-500">
            Date
          </th>
          <th className="pb-2 text-left text-xs font-medium text-slate-500">
            Note
          </th>
          <th />
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-50">
        {dates.map((d) => (
          <tr key={d.id}>
            <td className="py-2 pr-4 text-slate-700">
              {formatImportantDateType(
                d.type as import("@/types").ImportantDateType
              )}
            </td>
            <td className="py-2 pr-4 text-slate-600 whitespace-nowrap font-mono text-xs">
              {formatDate(d.date_time)}
            </td>
            <td className="py-2 pr-4 text-slate-400 text-xs">
              {d.note ?? ""}
            </td>
            <td className="py-2">
              <button
                aria-label="Delete date"
                className="text-slate-300 hover:text-red-500 transition-colors"
                onClick={() => deleteDate.mutate(d.id)}
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
