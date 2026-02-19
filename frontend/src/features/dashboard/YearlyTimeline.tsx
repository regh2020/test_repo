import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { conferencesApi } from "@/api";
import { qk } from "@/utils/queryKeys";
import { formatDate } from "@/utils/date";
import { ROUTES } from "@/router/routes";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { SpinnerPage } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { CalendarDays } from "lucide-react";
import type { ConferenceTimelineItem } from "@/types";

// ─── Constants ────────────────────────────────────────────────────────────────

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const PALETTE = [
  "#3b82f6", // blue-500
  "#10b981", // emerald-500
  "#f59e0b", // amber-500
  "#ef4444", // red-500
  "#8b5cf6", // violet-500
  "#06b6d4", // cyan-500
  "#f97316", // orange-500
  "#ec4899", // pink-500
  "#14b8a6", // teal-500
  "#6366f1", // indigo-500
  "#84cc16", // lime-500
  "#a855f7", // purple-500
];

const STRIP_HEIGHT_PX = 14;
const ROW_HEIGHT_PX = 26;
const DEADLINE_AREA_PX = 18; // space below strip for deadline marker
const GAP_PCT = 0.5; // minimum gap between strips in %

// ─── Helpers ──────────────────────────────────────────────────────────────────

function isLeapYear(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
}

function daysInYear(year: number): number {
  return isLeapYear(year) ? 366 : 365;
}

function getDayOfYear(date: Date): number {
  const start = new Date(date.getFullYear(), 0, 0);
  return Math.floor((date.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
}

function toPct(dateStr: string, year: number): number {
  const d = new Date(dateStr);
  if (d.getFullYear() !== year) return -1;
  return Math.max(0, Math.min(100, ((getDayOfYear(d) - 1) / daysInYear(year)) * 100));
}

/** djb2 hash → stable palette index */
function confColor(id: string): string {
  let hash = 5381;
  for (let i = 0; i < id.length; i++) {
    hash = ((hash << 5) + hash) ^ id.charCodeAt(i);
    hash = hash >>> 0; // keep unsigned 32-bit
  }
  return PALETTE[hash % PALETTE.length];
}

/** Month label left position as % */
function monthPosition(month: number, year: number): number {
  const d = new Date(year, month, 1);
  return ((getDayOfYear(d) - 1) / daysInYear(year)) * 100;
}

// ─── Row packing ──────────────────────────────────────────────────────────────

interface PlacedConf {
  conf: ConferenceTimelineItem;
  startPct: number;
  endPct: number;
  row: number;
  color: string;
  deadlinePct: number | null;
}

function assignRows(confs: ConferenceTimelineItem[], year: number): PlacedConf[] {
  const placed: PlacedConf[] = [];
  // Track end position of last strip in each row
  const rowEnds: number[] = [];

  // Sort by start position
  const sorted = [...confs].sort((a, b) => {
    const as = a.start_date ? toPct(a.start_date, year) : 101;
    const bs = b.start_date ? toPct(b.start_date, year) : 101;
    return as - bs;
  });

  for (const conf of sorted) {
    if (!conf.start_date) continue;
    const startPct = toPct(conf.start_date, year);
    if (startPct < 0) continue;

    const endPct = conf.end_date
      ? Math.max(startPct + 1, toPct(conf.end_date, year))
      : startPct + 1.5; // minimal width for single-day

    const deadlinePct =
      conf.submission_deadline ? toPct(conf.submission_deadline, year) : null;

    const color = confColor(conf.id);

    // Find a row where the strip fits (with gap)
    let row = 0;
    for (let r = 0; r < rowEnds.length; r++) {
      if (rowEnds[r] + GAP_PCT <= startPct) {
        row = r;
        break;
      }
      row = r + 1;
    }

    while (rowEnds.length <= row) rowEnds.push(-Infinity);
    rowEnds[row] = endPct;

    placed.push({ conf, startPct, endPct, row, color, deadlinePct });
  }

  return placed;
}

// ─── Tooltip state ────────────────────────────────────────────────────────────

interface TooltipState {
  text: string;
  subtitle: string;
  x: number; // percent
  rowTop: number; // px from top of timeline area
}

// ─── Main component ────────────────────────────────────────────────────────────

export function YearlyTimeline() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const navigate = useNavigate();

  const { data, isPending, isError, error } = useQuery({
    queryKey: qk.conferences.timeline(year),
    queryFn: () => conferencesApi.getTimeline(year),
  });

  if (isPending) return <SpinnerPage />;
  if (isError) return <ErrorMessage error={error} />;

  const items = data as ConferenceTimelineItem[];
  const placed = assignRows(items, year);
  const numRows = placed.length > 0 ? Math.max(...placed.map((p) => p.row)) + 1 : 0;
  const timelineHeight = numRows * (ROW_HEIGHT_PX + DEADLINE_AREA_PX) + 8;

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
        {placed.length === 0 ? (
          <EmptyState
            icon={CalendarDays}
            title={`No conferences for ${year}`}
            description="Add conferences with start dates to see them here."
          />
        ) : (
          <div
            className="select-none"
            onMouseLeave={() => setTooltip(null)}
          >
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

            {/* Ruler bar with month ticks */}
            <div className="relative h-1.5 bg-slate-100 rounded-full mb-3">
              {MONTHS.map((m, idx) => (
                <div
                  key={m}
                  className="absolute w-px h-2 bg-slate-300 -top-0.5"
                  style={{ left: `${monthPosition(idx, year)}%` }}
                />
              ))}
            </div>

            {/* Timeline strips area */}
            <div
              className="relative overflow-visible"
              style={{ height: `${timelineHeight}px` }}
            >
              {placed.map(({ conf, startPct, endPct, row, color, deadlinePct }) => {
                const rowTopPx = row * (ROW_HEIGHT_PX + DEADLINE_AREA_PX);
                const stripW = Math.max(0.8, endPct - startPct);
                const label = conf.acronym || conf.name.slice(0, 10);
                const location = [conf.city, conf.country].filter(Boolean).join(", ");

                return (
                  <div key={conf.id}>
                    {/* Conference duration strip */}
                    <div
                      className="absolute cursor-pointer rounded-sm flex items-center px-1 overflow-hidden"
                      style={{
                        left: `${startPct}%`,
                        width: `${stripW}%`,
                        top: `${rowTopPx}px`,
                        height: `${STRIP_HEIGHT_PX}px`,
                        backgroundColor: color,
                        opacity: 0.85,
                        minWidth: "4px",
                      }}
                      onClick={() => navigate(ROUTES.conferenceDetail(conf.id))}
                      onMouseEnter={() =>
                        setTooltip({
                          text: conf.name,
                          subtitle: [
                            conf.start_date ? formatDate(conf.start_date) : null,
                            conf.end_date ? `– ${formatDate(conf.end_date)}` : null,
                            location || null,
                          ]
                            .filter(Boolean)
                            .join(" "),
                          x: (startPct + endPct) / 2,
                          rowTop: rowTopPx,
                        })
                      }
                    >
                      {stripW > 5 && (
                        <span className="text-white text-[10px] font-semibold leading-none truncate pointer-events-none">
                          {label}
                        </span>
                      )}
                    </div>

                    {/* Submission deadline marker */}
                    {deadlinePct !== null && deadlinePct >= 0 && (
                      <div
                        className="absolute cursor-pointer"
                        style={{
                          left: `${deadlinePct}%`,
                          top: `${rowTopPx + STRIP_HEIGHT_PX}px`,
                          transform: "translateX(-50%)",
                          width: "2px",
                          height: `${DEADLINE_AREA_PX - 4}px`,
                        }}
                        onClick={() => navigate(ROUTES.conferenceDetail(conf.id))}
                        onMouseEnter={() =>
                          setTooltip({
                            text: conf.name,
                            subtitle: `Submission deadline: ${conf.submission_deadline ? formatDate(conf.submission_deadline) : ""}`,
                            x: deadlinePct,
                            rowTop: rowTopPx,
                          })
                        }
                      >
                        {/* Dashed stem */}
                        <div
                          style={{
                            width: "2px",
                            height: "100%",
                            borderLeft: `2px dashed ${color}`,
                            opacity: 0.7,
                          }}
                        />
                        {/* Dot */}
                        <div
                          style={{
                            width: "8px",
                            height: "8px",
                            borderRadius: "50%",
                            backgroundColor: color,
                            position: "absolute",
                            bottom: "-4px",
                            left: "-3px",
                          }}
                        />
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Tooltip */}
              {tooltip && (
                <div
                  className="absolute z-30 pointer-events-none"
                  style={{
                    left: `${Math.min(85, Math.max(5, tooltip.x))}%`,
                    top: `${Math.max(0, tooltip.rowTop - 56)}px`,
                    transform: "translateX(-50%)",
                  }}
                >
                  <div className="bg-slate-900 text-white rounded-lg shadow-xl px-3 py-2 text-sm max-w-64">
                    <p className="font-semibold leading-snug">{tooltip.text}</p>
                    {tooltip.subtitle && (
                      <p className="text-slate-300 text-xs mt-0.5 leading-snug">{tooltip.subtitle}</p>
                    )}
                  </div>
                  {/* Arrow */}
                  <div className="flex justify-center">
                    <div className="w-2 h-2 bg-slate-900 rotate-45 -mt-1" />
                  </div>
                </div>
              )}
            </div>

            {/* Legend hint */}
            <p className="text-xs text-slate-400 mt-2">
              Strips show conference duration · Dashed markers show submission deadlines · Click to view
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
