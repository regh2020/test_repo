import type { ConferenceFilters } from "@/types";

/**
 * Centralised TanStack Query key factory.
 * Keeps query keys consistent and easy to invalidate.
 */
export const qk = {
  // Conferences
  conferences: {
    all: ["conferences"] as const,
    lists: () => [...qk.conferences.all, "list"] as const,
    list: (filters: ConferenceFilters) =>
      [...qk.conferences.lists(), filters] as const,
    details: () => [...qk.conferences.all, "detail"] as const,
    detail: (id: string) => [...qk.conferences.details(), id] as const,
    dates: (id: string) => [...qk.conferences.detail(id), "dates"] as const,
    sources: (id: string) => [...qk.conferences.detail(id), "sources"] as const,
  },

  // Discovery
  discovery: {
    all: ["discovery"] as const,
    run: (id: string) => [...qk.discovery.all, id] as const,
  },

  // Refresh
  refresh: {
    all: ["refresh"] as const,
  },
};
