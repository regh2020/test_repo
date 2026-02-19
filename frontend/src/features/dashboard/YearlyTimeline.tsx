import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { conferencesApi } from "@/api";
import { qk } from "@/utils/queryKeys";
import { formatImportantDateType } from "@/utils/format";
import { formatDate } from "@/utils/date";
import { ROUTES } from "@/router/routes";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { SpinnerPage } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { CalendarDays } from "lucide-react";
import type { GlobalImportantDate, ImportantDateType } from "@/types";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function getDayOfYear(date: Date): number {
  const start = new Date(date.getFullYear(), 0, 0);
  const diff = date.getTime() - start.getTime();
  const oneDay = 1000 * 60 * 60 * 24;
  return Math.floor(diff / oneDay);
}

function isLeapYear(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
}

function daysInYear(year: number): number {
  return isLeapYear(year) ? 366 : 365;
}

/** Position of a month label as percentage 0..100 */
function monthPosition(month: number, year: number): number {
  const d = new Date(year, month, 1);
  return ((getDayOfYear(d) - 1) / daysInYear(year)) * 100;
}

// Color per date type
const TYPE_COLORS: Partial<Record<ImportantDateType, string>> = {
  submission_deadline: "bg-rose-500",
  abstract_submission_deadline: "bg-orange-400",
  notification_date: "bg-amber-500",
  camera_ready_deadline: "bg-yellow-500",
  conference_start_date: "bg-emerald-500",
  conference_end_date: "bg-teal-500",
  workshop_deadline: "bg-violet-500",
  registration_deadline: "bg-blue-500",
  other: "bg-slate-400",
};

function typeColor(type: string): string {
  return TYPE_COLORS[type as ImportantDateType] ?? "bg-slate-400";
}

interface TimelineEvent {
  id: string;
  label: string;
  fullName: string;
  dateStr: string;
  dateType: string;
  position: number; // 0..100 percent
  conferenceId: string;
}

export function YearlyTimeline() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);

  const { data, isPending, isError, error } = useQuery({
    queryKey: qk.globalDates.all,
    queryFn: () => conferencesApi.listGlobalImportantDates(),
  });

  if (isPending) return <SpinnerPage />;
  if (isError) return <ErrorMessage error={error} />;

  const totalDays = daysInYear(year);

  // Filter and sort events for the selected year
  const events: TimelineEvent[] = (data as GlobalImportantDate[])
    .filter((item) => {
      const d = new Date(item.date.date_time);
      return d.getFullYear() === year;
    })
    .map((item) => {
      const d = new Date(item.date.date_time);
      const dayOfYear = getDayOfYear(d);
      const position = ((dayOfYear - 1) / totalDays) * 100;
      return {
        id: item.date.id,
        label: item.conference.acronym || item.conference.name.slice(0, 8),
        fullName: item.conference.name,
        dateStr: formatDate(item.date.date_time),
        dateType: formatImportantDateType(item.date.type as ImportantDateType),
        position: Math.max(0, Math.min(100, position)),
        conferenceId: item.conference.id,
      };
    })
    .sort((a, b) => a.position - b.position);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CalendarDays className="h-4 w-4 text-brand-600" />
            <CardTitle>Yearly Timeline</CardTitle>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <button
              className="text-slate-400 hover:text-slate-700 px-1"
              onClick={() => setYear((y) => y - 1)}
              aria-label="Previous year"
            >
              ‹
            </button>
            <span className="font-medium text-slate-700 w-12 text-center">{year}</span>
            <button
              className="text-slate-400 hover:text-slate-700 px-1"
              onClick={() => setYear((y) => y + 1)}
              aria-label="Next year"
            >
              ›
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {events.length === 0 ? (
          <EmptyState
            icon={CalendarDays}
            title={`No events for ${year}`}
            description="Add conferences with important dates to see them here."
          />
        ) : (
          <div className="select-none">
            {/* Month labels */}
            <div className="relative h-5 mb-1">
              {MONTHS.map((m, idx) => (
                <span
                  key={m}
                  className="absolute text-xs text-slate-400 -translate-x-1/2"
                  style={{ left: `${monthPosition(idx, year)}%` }}
                >
                  {m}
                </span>
              ))}
            </div>

            {/* Timeline bar */}
            <div className="relative h-1.5 bg-slate-100 rounded-full mb-8">
              {/* Month tick marks */}
              {MONTHS.map((m, idx) => (
                <div
                  key={m}
                  className="absolute w-px h-2 bg-slate-200 -top-0.5"
                  style={{ left: `${monthPosition(idx, year)}%` }}
                />
              ))}
            </div>

            {/* Events */}
            <div className="relative" style={{ height: `${Math.max(48, events.length * 28)}px` }}>
              {events.map((evt, i) => (
                <TimelineMarker key={evt.id} event={evt} index={i} total={events.length} />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function TimelineMarker({
  event,
  index,
  total,
}: {
  event: TimelineEvent;
  index: number;
  total: number;
}) {
  const [showTooltip, setShowTooltip] = useState(false);
  // Stack events vertically to avoid overlaps
  const row = index % Math.max(1, Math.ceil(total / 3));
  const topPx = row * 28;

  return (
    <div
      className="absolute"
      style={{ left: `${event.position}%`, top: `${topPx}px` }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {/* Dot marker */}
      <div className={`w-2.5 h-2.5 rounded-full ${typeColor(event.dateType)} shadow-sm -translate-x-1/2 cursor-pointer`} />

      {/* Label */}
      <div className="absolute top-3 left-0 -translate-x-1/2 whitespace-nowrap">
        <span className="text-xs text-slate-600 font-medium">{event.label}</span>
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div className="absolute z-20 bottom-6 left-1/2 -translate-x-1/2 bg-white border border-slate-200 rounded-lg shadow-lg p-3 min-w-48 max-w-64">
          <Link
            to={ROUTES.conferenceDetail(event.conferenceId)}
            className="block text-sm font-medium text-brand-700 hover:underline mb-1 leading-snug"
          >
            {event.fullName}
          </Link>
          <p className="text-xs text-slate-500">{event.dateType}</p>
          <p className="text-xs text-slate-400 mt-0.5">{event.dateStr}</p>
        </div>
      )}
    </div>
  );
}
