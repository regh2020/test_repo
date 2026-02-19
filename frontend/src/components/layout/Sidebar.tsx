import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  ListFilter,
  Link2,
  Search,
  RefreshCw,
  GraduationCap,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { ROUTES } from "@/router";

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  end?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  {
    to: ROUTES.dashboard,
    label: "Dashboard",
    icon: LayoutDashboard,
    end: true,
  },
  {
    to: ROUTES.conferences,
    label: "Conferences",
    icon: ListFilter,
  },
  {
    to: ROUTES.ingestion,
    label: "Ingest URL",
    icon: Link2,
  },
  {
    to: ROUTES.discovery,
    label: "Discover",
    icon: Search,
  },
  {
    to: ROUTES.refresh,
    label: "Refresh Status",
    icon: RefreshCw,
  },
];

export function Sidebar() {
  return (
    <aside className="flex flex-col w-56 shrink-0 border-r border-slate-200 bg-white min-h-screen">
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-4 h-14 border-b border-slate-200">
        <GraduationCap className="w-6 h-6 text-brand-600 shrink-0" />
        <span className="font-semibold text-slate-900 text-sm tracking-tight">
          ConferenceHub
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-0.5">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )
            }
          >
            <item.icon
              className={cn("h-4 w-4 shrink-0")}
            />
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-slate-100">
        <p className="text-[11px] text-slate-400">
          Academic Events Registry
        </p>
      </div>
    </aside>
  );
}
