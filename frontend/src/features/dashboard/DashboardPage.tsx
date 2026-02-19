import { Link } from "react-router-dom";
import { CalendarDays, Clock, ArrowRight, PlusCircle } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { SpinnerPage } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate, formatDateRange, timeAgo } from "@/utils/date";
import { ROUTES } from "@/router/routes";
import { useUpcomingConferences, useRecentConferences } from "./useDashboard";
import { YearlyTimeline } from "./YearlyTimeline";
import type { Conference } from "@/types";

export function DashboardPage() {
  const upcoming = useUpcomingConferences(6);
  const recent = useRecentConferences(6);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of your academic conferences registry."
        actions={
          <Button asChild size="sm">
            <Link to={ROUTES.conferenceNew}>
              <PlusCircle className="h-4 w-4" />
              Add Conference
            </Link>
          </Button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming conferences */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CalendarDays className="h-4 w-4 text-brand-600" />
                <CardTitle>Upcoming Conferences</CardTitle>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link to={`${ROUTES.conferences}?status=upcoming`}>
                  View all <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {upcoming.isPending && <SpinnerPage />}
            {upcoming.isError && <ErrorMessage error={upcoming.error} />}
            {upcoming.isSuccess && upcoming.data.length === 0 && (
              <EmptyState
                icon={CalendarDays}
                title="No upcoming conferences"
                description="Add a conference or ingest a URL to get started."
              />
            )}
            {upcoming.isSuccess && upcoming.data.length > 0 && (
              <ul className="divide-y divide-slate-100">
                {upcoming.data.map((conf) => (
                  <ConferenceListItem key={conf.id} conf={conf} />
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Recently updated */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-brand-600" />
                <CardTitle>Recently Updated</CardTitle>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link to={ROUTES.conferences}>
                  View all <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {recent.isPending && <SpinnerPage />}
            {recent.isError && <ErrorMessage error={recent.error} />}
            {recent.isSuccess && recent.data.length === 0 && (
              <EmptyState
                icon={Clock}
                title="No conferences yet"
                description="Start by ingesting a conference URL."
              />
            )}
            {recent.isSuccess && recent.data.length > 0 && (
              <ul className="divide-y divide-slate-100">
                {recent.data.map((conf) => (
                  <ConferenceListItem key={conf.id} conf={conf} showUpdated />
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Yearly Timeline */}
      <div className="mt-6">
        <YearlyTimeline />
      </div>
    </div>
  );
}

function ConferenceListItem({
  conf,
  showUpdated = false,
}: {
  conf: Conference;
  showUpdated?: boolean;
}) {
  return (
    <li className="py-3 flex items-start justify-between gap-4 group">
      <div className="min-w-0">
        <Link
          to={ROUTES.conferenceDetail(conf.id)}
          className="text-sm font-medium text-slate-800 hover:text-brand-700 truncate block"
        >
          {conf.acronym ? `${conf.acronym} — ` : ""}
          {conf.name}
        </Link>
        <p className="text-xs text-slate-400 mt-0.5">
          {showUpdated
            ? `Updated ${timeAgo(conf.updated_at)}`
            : formatDateRange(conf.start_date, conf.end_date)}
          {conf.city && !showUpdated && ` · ${conf.city}`}
          {conf.country && !showUpdated && `, ${conf.country}`}
        </p>
      </div>
      <StatusBadge status={conf.status} />
    </li>
  );
}
