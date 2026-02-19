# Frontend Architecture

Academic Events & Conferences Registry — frontend codebase.

---

## Tech Stack

| Concern | Library |
|---|---|
| UI framework | React 18 + TypeScript 5 |
| Build tool | Vite 5 |
| Routing | React Router 6 (data router) |
| Server state | TanStack Query v5 |
| Forms | React Hook Form + Zod |
| Styling | Tailwind CSS 3 |
| UI primitives | Radix UI |
| HTTP client | Axios |
| Date handling | date-fns |
| Icons | lucide-react |

---

## Directory Structure

```
src/
├── api/                    # API client layer (one module per domain)
│   ├── client.ts           # Axios instance + error interceptor
│   ├── conferences.ts      # Conference CRUD + dates + sources
│   ├── discovery.ts        # Discovery + import
│   ├── ingestion.ts        # URL ingestion
│   ├── refresh.ts          # Source refresh
│   └── index.ts
│
├── types/                  # TypeScript domain types (mirrors backend schemas)
│   ├── conference.ts
│   ├── discovery.ts
│   ├── ingestion.ts
│   ├── refresh.ts
│   └── index.ts
│
├── utils/
│   ├── cn.ts               # Tailwind class merger (clsx + twMerge)
│   ├── date.ts             # Date formatting helpers
│   ├── format.ts           # Domain-specific formatters
│   └── queryKeys.ts        # TanStack Query key factory
│
├── router/
│   ├── index.tsx           # createBrowserRouter with all routes
│   ├── NotFoundPage.tsx
│   └── ErrorBoundaryPage.tsx
│
├── components/
│   ├── ui/                 # Reusable, headless-style UI primitives
│   │   ├── Button.tsx      # CVA-powered variants
│   │   ├── Badge.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   ├── Textarea.tsx
│   │   ├── Label.tsx
│   │   ├── Spinner.tsx
│   │   ├── EmptyState.tsx
│   │   ├── ErrorMessage.tsx
│   │   ├── ConfidenceBar.tsx
│   │   ├── StatusBadge.tsx
│   │   └── FormField.tsx
│   │
│   └── layout/             # Shell and page layout
│       ├── AppShell.tsx    # Root layout (sidebar + outlet)
│       ├── Sidebar.tsx     # Navigation
│       └── PageHeader.tsx
│
├── features/               # Feature-based domain modules
│   ├── dashboard/
│   │   ├── DashboardPage.tsx
│   │   └── useDashboard.ts
│   │
│   ├── conferences/
│   │   ├── ConferenceListPage.tsx   # Search, filter, sort, paginate
│   │   ├── ConferenceDetailPage.tsx # Full detail + dates + sources
│   │   ├── ConferenceFormPage.tsx   # Create / edit form
│   │   ├── AddSourceDialog.tsx
│   │   ├── AddDateDialog.tsx
│   │   └── useConferences.ts        # All queries + mutations
│   │
│   ├── ingestion/
│   │   ├── IngestionPage.tsx        # URL paste + result preview
│   │   └── useIngestion.ts
│   │
│   ├── discovery/
│   │   ├── DiscoveryPage.tsx        # Keyword search + candidate cards
│   │   └── useDiscovery.ts
│   │
│   └── refresh/
│       ├── RefreshPage.tsx              # Global refresh status + trigger
│       ├── RefreshConferenceButton.tsx  # Per-conference inline refresh
│       └── useRefresh.ts
│
├── styles/
│   └── globals.css         # Tailwind directives + CSS variables
│
└── main.tsx                # React root, QueryClient, RouterProvider
```

---

## Key Architectural Decisions

### Feature-based structure
Code is co-located by domain feature (conference, ingestion, discovery, refresh)
rather than by file type. Each feature owns its page components, hooks, and
sub-components.

### Server state only (TanStack Query)
There is no Redux or Zustand. All remote data lives in TanStack Query's cache.
Mutations invalidate affected query keys so the UI stays consistent.
`queryKeys.ts` is the single source of truth for cache keys.

### API layer isolation
All HTTP calls go through `src/api/`. Pages and hooks never import axios directly.
The axios instance in `client.ts` normalises errors into `ApiError` before they
reach application code.

### AI call efficiency (backend contract)
The backend only invokes the Anthropic API when a source's content hash changes.
The `RefreshPage` exposes this contract to the user with a "Force refresh" toggle
that bypasses the hash check. The frontend never calls the AI directly.

### Typed forms with Zod
Every form schema doubles as the TypeScript type via `z.infer`. React Hook Form
`zodResolver` validates at submission time. Field-level errors are displayed
inline via `FormField`.

### Routing
React Router 6 data router with `createBrowserRouter`. An `ErrorBoundaryPage`
catches unhandled route errors. All route paths are centralised in `ROUTES`.

---

## Running Locally

```bash
cd frontend
npm install
npm run dev        # Starts Vite dev server on :5173, proxies /api → :8000
```

Backend must be running at `http://localhost:8000`.

## Building for Production

```bash
npm run build      # Type-checks then builds to dist/
npm run preview    # Serves the dist/ folder locally
```
