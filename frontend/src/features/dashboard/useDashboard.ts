import { useQuery } from "@tanstack/react-query";
import { conferencesApi } from "@/api";
import { qk } from "@/utils/queryKeys";
import { parseDate } from "@/utils/date";
import type { Conference } from "@/types";

const today = () => new Date().toISOString().slice(0, 10);

/** Conferences starting from today, soonest first. */
export function useUpcomingConferences(limit = 5) {
  return useQuery({
    queryKey: qk.conferences.list({ status: "upcoming", limit }),
    queryFn: () =>
      conferencesApi.list({ status: "upcoming", start_after: today(), limit }),
    select: (data: Conference[]) =>
      [...data].sort((a, b) => {
        const da = parseDate(a.start_date)?.getTime() ?? Infinity;
        const db = parseDate(b.start_date)?.getTime() ?? Infinity;
        return da - db;
      }),
  });
}

/** Most recently updated conferences. */
export function useRecentConferences(limit = 5) {
  return useQuery({
    queryKey: qk.conferences.list({ limit }),
    queryFn: () => conferencesApi.list({ limit }),
    select: (data: Conference[]) =>
      [...data]
        .sort(
          (a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        )
        .slice(0, limit),
  });
}
