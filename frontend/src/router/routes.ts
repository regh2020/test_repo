/**
 * Centralised route path constants.
 *
 * Kept in a separate file so that layout components (Sidebar, etc.) can
 * import route paths without pulling in the full router module and creating
 * a circular dependency:
 *   router/index.tsx → AppShell → Sidebar → router/index.tsx
 */
export const ROUTES = {
  dashboard: "/",
  conferences: "/conferences",
  conferenceNew: "/conferences/new",
  conferenceDetail: (id = ":id") => `/conferences/${id}`,
  conferenceEdit: (id = ":id") => `/conferences/${id}/edit`,
  ingestion: "/ingest",
  discovery: "/discover",
  refresh: "/refresh",
} as const;
