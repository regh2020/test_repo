import { Link } from "react-router-dom";
import { Calendar } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { SpinnerPage } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { ROUTES } from "@/router/routes";
import { formatDate, timeAgo } from "@/utils/date";
import { formatImportantDateType } from "@/utils/format";
import { useGlobalImportantDates } from "../conferences/useConferences";
import type { GlobalImportantDate, ImportantDateType } from "@/types";

export function ImportantDatesPage() {
  const { data, isPending, isError, error } = useGlobalImportantDates();

  const now = new Date().toISOString();
  const future = (data ?? []).filter((g) => g.date.date_time >= now).sort(
    (a, b) => a.date.date_time.localeCompare(b.date.date_time)
  );
  const past = (data ?? [])
    .filter((g) => g.date.date_time < now)
    .sort((a, b) => b.date.date_time.localeCompare(a.date.date_time));

  return (
    <div>
      <PageHeader
        title="Important Dates"
        description="Upcoming and past key dates across all conferences."
      />

      {isPending && <SpinnerPage />}
      {isError && <ErrorMessage error={error} />}

      {data && data.length === 0 && (
        <EmptyState
          icon={Calendar}
          title="No important dates"
          description="Add submission deadlines and conference dates to see them here."
        />
      )}

      {data && data.length > 0 && (
        <div className="space-y-8">
          {/* Future dates */}
          <section>
            <h2 className="text-base font-semibold text-slate-800 mb-3">
              Upcoming
            </h2>
            {future.length === 0 ? (
              <p className="text-sm text-slate-400">No upcoming dates.</p>
            ) : (
              <DatesTable items={future} past={false} />
            )}
          </section>

          {/* Past dates */}
          <section>
            <h2 className="text-base font-semibold text-slate-800 mb-3">
              Past
            </h2>
            {past.length === 0 ? (
              <p className="text-sm text-slate-400">No past dates.</p>
            ) : (
              <DatesTable items={past} past={true} />
            )}
          </section>
        </div>
      )}
    </div>
  );
}

function DatesTable({
  items,
  past,
}: {
  items: GlobalImportantDate[];
  past: boolean;
}) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50">
            <th className="px-4 py-2.5 text-left font-medium text-slate-600">
              Date
            </th>
            <th className="px-4 py-2.5 text-left font-medium text-slate-600">
              Conference
            </th>
            <th className="px-4 py-2.5 text-left font-medium text-slate-600">
              Type
            </th>
            <th className="px-4 py-2.5 text-left font-medium text-slate-600">
              Location
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {items.map((g) => (
            <tr
              key={g.date.id}
              className={past ? "opacity-60" : "hover:bg-slate-50 transition-colors"}
            >
              <td
                className={`px-4 py-3 font-mono text-xs whitespace-nowrap ${
                  past ? "line-through text-slate-400" : "text-slate-700"
                }`}
              >
                {formatDate(g.date.date_time)}
              </td>
              <td className="px-4 py-3">
                <Link
                  to={ROUTES.conferenceDetail(g.conference.id)}
                  className="font-medium text-brand-600 hover:underline"
                >
                  {g.conference.acronym
                    ? `${g.conference.acronym} — ${g.conference.name}`
                    : g.conference.name}
                </Link>
              </td>
              <td className="px-4 py-3 text-slate-500">
                {formatImportantDateType(g.date.type as ImportantDateType)}
              </td>
              <td className="px-4 py-3 text-slate-400 text-xs">
                {[g.conference.city, g.conference.country]
                  .filter(Boolean)
                  .join(", ") || (g.conference.is_online ? "Online" : "—")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
