import { useState, useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  PlusCircle,
  Search,
  SlidersHorizontal,
  ListOrdered,
  LayoutGrid,
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { SpinnerPage } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Badge } from "@/components/ui/Badge";
import { ROUTES } from "@/router/routes";
import { formatDateRange, formatDate, timeAgo } from "@/utils/date";
import { useConferences } from "./useConferences";
import type { Conference, ConferenceFilters, ConferenceStatus } from "@/types";

const STATUS_OPTIONS: Array<{ value: ConferenceStatus | ""; label: string }> = [
  { value: "", label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "past", label: "Past" },
  { value: "cancelled", label: "Cancelled" },
  { value: "postponed", label: "Postponed" },
];

type SortColumn =
  | "name"
  | "start_date"
  | "location"
  | "submission_deadline"
  | "status"
  | "updated_at";

type ViewMode = "table" | "cards";

export function ConferenceListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [viewMode, setViewMode] = useState<ViewMode>("table");

  // Read filters from URL for shareable links
  const nameSearch = searchParams.get("name") ?? "";
  const statusFilter = (searchParams.get("status") ?? "") as ConferenceStatus | "";
  const topicFilter = searchParams.get("topic") ?? "";
  const sortBy = (searchParams.get("sort_by") ?? "start_date") as SortColumn;
  const sortOrder = (searchParams.get("sort_order") ?? "asc") as "asc" | "desc";

  const [page, setPage] = useState(0);
  const pageSize = 25;

  const filters: ConferenceFilters = {
    ...(nameSearch ? { name: nameSearch } : {}),
    ...(statusFilter ? { status: statusFilter } : {}),
    ...(topicFilter ? { topic: topicFilter } : {}),
    sort_by: sortBy,
    sort_order: sortOrder,
    limit: pageSize,
    offset: page * pageSize,
  };

  const { data, isPending, isError, error } = useConferences(filters);

  const setFilter = useCallback(
    (key: string, value: string) => {
      setPage(0);
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        if (value) next.set(key, value);
        else next.delete(key);
        return next;
      });
    },
    [setSearchParams]
  );

  const handleSort = useCallback(
    (column: SortColumn) => {
      setPage(0);
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        const currentCol = prev.get("sort_by") ?? "start_date";
        const currentOrder = prev.get("sort_order") ?? "asc";
        if (currentCol === column) {
          next.set("sort_order", currentOrder === "asc" ? "desc" : "asc");
        } else {
          next.set("sort_by", column);
          next.set("sort_order", "asc");
        }
        return next;
      });
    },
    [setSearchParams]
  );

  return (
    <div>
      <PageHeader
        title="Conferences"
        description="Browse, search and manage all tracked academic conferences."
        actions={
          <Button asChild size="sm">
            <Link to={ROUTES.conferenceNew}>
              <PlusCircle className="h-4 w-4" />
              Add Conference
            </Link>
          </Button>
        }
      />

      {/* Filters bar */}
      <div className="flex flex-wrap items-center gap-2 mb-5">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          <Input
            placeholder="Search by name…"
            className="pl-8"
            value={nameSearch}
            onChange={(e) => setFilter("name", e.target.value)}
          />
        </div>

        <select
          className="h-9 rounded-md border border-slate-200 bg-white px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          value={statusFilter}
          onChange={(e) => setFilter("status", e.target.value)}
          aria-label="Filter by status"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>

        <Input
          placeholder="Topic…"
          className="w-36"
          value={topicFilter}
          onChange={(e) => setFilter("topic", e.target.value)}
        />

        <div className="ml-auto flex items-center gap-1">
          <Button
            variant={viewMode === "table" ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setViewMode("table")}
            aria-label="Table view"
          >
            <ListOrdered className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "cards" ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setViewMode("cards")}
            aria-label="Card view"
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {isPending && <SpinnerPage />}
      {isError && <ErrorMessage error={error} />}

      {data && data.length === 0 && (
        <EmptyState
          icon={SlidersHorizontal}
          title="No conferences found"
          description="Try adjusting your search or filters."
        />
      )}

      {data && data.length > 0 && viewMode === "table" && (
        <ConferenceTable
          conferences={data}
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSort={handleSort}
        />
      )}

      {data && data.length > 0 && viewMode === "cards" && (
        <ConferenceCardGrid conferences={data} />
      )}

      {/* Pagination */}
      {data && (
        <div className="flex items-center justify-between mt-5 text-sm text-slate-500">
          <span>
            {data.length === pageSize
              ? `Showing ${page * pageSize + 1}–${page * pageSize + data.length}`
              : `${page * pageSize + data.length} result${data.length !== 1 ? "s" : ""}`}
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={data.length < pageSize}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Sortable column header ────────────────────────────────────────────────────

function SortableHeader({
  column,
  label,
  sortBy,
  sortOrder,
  onSort,
}: {
  column: SortColumn;
  label: string;
  sortBy: SortColumn;
  sortOrder: "asc" | "desc";
  onSort: (col: SortColumn) => void;
}) {
  const active = sortBy === column;
  return (
    <th className="px-4 py-2.5 text-left font-medium text-slate-600">
      <button
        className="flex items-center gap-1 hover:text-slate-900 transition-colors"
        onClick={() => onSort(column)}
        aria-label={`Sort by ${label}`}
      >
        {label}
        {active ? (
          sortOrder === "asc" ? (
            <ChevronUp className="h-3.5 w-3.5 text-brand-500" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5 text-brand-500" />
          )
        ) : (
          <ChevronsUpDown className="h-3.5 w-3.5 text-slate-300" />
        )}
      </button>
    </th>
  );
}

// ─── Table view ───────────────────────────────────────────────────────────────

function ConferenceTable({
  conferences,
  sortBy,
  sortOrder,
  onSort,
}: {
  conferences: Conference[];
  sortBy: SortColumn;
  sortOrder: "asc" | "desc";
  onSort: (col: SortColumn) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50">
            <SortableHeader column="name" label="Conference" sortBy={sortBy} sortOrder={sortOrder} onSort={onSort} />
            <SortableHeader column="start_date" label="Dates" sortBy={sortBy} sortOrder={sortOrder} onSort={onSort} />
            <SortableHeader column="location" label="Location" sortBy={sortBy} sortOrder={sortOrder} onSort={onSort} />
            <th className="px-4 py-2.5 text-left font-medium text-slate-600">Topics</th>
            <SortableHeader column="submission_deadline" label="Submission Deadline" sortBy={sortBy} sortOrder={sortOrder} onSort={onSort} />
            <SortableHeader column="status" label="Status" sortBy={sortBy} sortOrder={sortOrder} onSort={onSort} />
            <SortableHeader column="updated_at" label="Updated" sortBy={sortBy} sortOrder={sortOrder} onSort={onSort} />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {conferences.map((conf) => (
            <tr key={conf.id} className="hover:bg-slate-50 transition-colors">
              <td className="px-4 py-3 max-w-xs">
                <Link
                  to={ROUTES.conferenceDetail(conf.id)}
                  className="font-medium text-slate-800 hover:text-brand-700"
                >
                  {conf.acronym && (
                    <span className="text-brand-600 mr-1">{conf.acronym}</span>
                  )}
                  {conf.name}
                </Link>
              </td>
              <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                {formatDateRange(conf.start_date, conf.end_date)}
              </td>
              <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                {[conf.city, conf.country].filter(Boolean).join(", ") || "—"}
                {conf.is_online && (
                  <Badge variant="secondary" className="ml-1.5">
                    Online
                  </Badge>
                )}
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {conf.topics.slice(0, 3).map((t) => (
                    <Badge key={t} variant="outline" className="text-xs">
                      {t}
                    </Badge>
                  ))}
                  {conf.topics.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{conf.topics.length - 3}
                    </Badge>
                  )}
                </div>
              </td>
              <td className="px-4 py-3 text-slate-500 whitespace-nowrap font-mono text-xs">
                {conf.submission_deadline ? formatDate(conf.submission_deadline) : "—"}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={conf.status} />
              </td>
              <td className="px-4 py-3 text-slate-400 whitespace-nowrap text-xs">
                {timeAgo(conf.updated_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Card grid view ───────────────────────────────────────────────────────────

function ConferenceCardGrid({ conferences }: { conferences: Conference[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {conferences.map((conf) => (
        <Link
          key={conf.id}
          to={ROUTES.conferenceDetail(conf.id)}
          className="group block rounded-lg border border-slate-200 bg-white p-4 hover:border-brand-300 hover:shadow-md transition-all"
        >
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="min-w-0">
              {conf.acronym && (
                <p className="text-xs font-semibold text-brand-600 mb-0.5">
                  {conf.acronym}
                </p>
              )}
              <h3 className="font-medium text-slate-900 text-sm leading-snug group-hover:text-brand-700 truncate">
                {conf.name}
              </h3>
            </div>
            <StatusBadge status={conf.status} />
          </div>

          <p className="text-xs text-slate-500 mb-2">
            {formatDateRange(conf.start_date, conf.end_date)}
            {conf.city && ` · ${conf.city}`}
          </p>

          {conf.submission_deadline && (
            <p className="text-xs text-amber-600 mb-2">
              Deadline: {conf.submission_deadline.slice(0, 10)}
            </p>
          )}

          <div className="flex flex-wrap gap-1">
            {conf.topics.slice(0, 4).map((t) => (
              <Badge key={t} variant="outline" className="text-[10px]">
                {t}
              </Badge>
            ))}
          </div>
        </Link>
      ))}
    </div>
  );
}
