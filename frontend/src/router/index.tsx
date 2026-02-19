import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { ConferenceListPage } from "@/features/conferences/ConferenceListPage";
import { ConferenceDetailPage } from "@/features/conferences/ConferenceDetailPage";
import { ConferenceFormPage } from "@/features/conferences/ConferenceFormPage";
import { IngestionPage } from "@/features/ingestion/IngestionPage";
import { DiscoveryPage } from "@/features/discovery/DiscoveryPage";
import { RefreshPage } from "@/features/refresh/RefreshPage";
import { NotFoundPage } from "./NotFoundPage";
import { ErrorBoundaryPage } from "./ErrorBoundaryPage";

// Re-export so callers that do `import { ROUTES } from "@/router"` still work,
// but the canonical definition lives in routes.ts (no dependencies) to break
// the circular import: router/index → layout → Sidebar → router/index.
export { ROUTES } from "./routes";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    errorElement: <ErrorBoundaryPage />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "conferences", element: <ConferenceListPage /> },
      { path: "conferences/new", element: <ConferenceFormPage mode="create" /> },
      { path: "conferences/:id", element: <ConferenceDetailPage /> },
      { path: "conferences/:id/edit", element: <ConferenceFormPage mode="edit" /> },
      { path: "ingest", element: <IngestionPage /> },
      { path: "discover", element: <DiscoveryPage /> },
      { path: "refresh", element: <RefreshPage /> },
      { path: "404", element: <NotFoundPage /> },
      { path: "*", element: <Navigate to="/404" replace /> },
    ],
  },
]);
