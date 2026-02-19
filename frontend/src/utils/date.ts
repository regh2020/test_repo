import {
  format,
  formatDistanceToNow,
  parseISO,
  isValid,
} from "date-fns";

export function parseDate(iso: string | null | undefined): Date | null {
  if (!iso) return null;
  const d = parseISO(iso);
  return isValid(d) ? d : null;
}

export function formatDate(
  iso: string | null | undefined,
  fmt = "MMM d, yyyy"
): string {
  const d = parseDate(iso);
  return d ? format(d, fmt) : "—";
}

export function formatDateTime(iso: string | null | undefined): string {
  const d = parseDate(iso);
  return d ? format(d, "MMM d, yyyy HH:mm") : "—";
}

export function timeAgo(iso: string | null | undefined): string {
  const d = parseDate(iso);
  return d ? formatDistanceToNow(d, { addSuffix: true }) : "—";
}

export function formatDateRange(
  start: string | null | undefined,
  end: string | null | undefined
): string {
  if (!start && !end) return "—";
  if (!end) return formatDate(start);
  if (!start) return formatDate(end);

  const s = parseDate(start);
  const e = parseDate(end);

  if (!s || !e) return "—";

  // Same year: "Jun 10 – 14, 2025"
  if (s.getFullYear() === e.getFullYear()) {
    if (s.getMonth() === e.getMonth()) {
      return `${format(s, "MMM d")} – ${format(e, "d, yyyy")}`;
    }
    return `${format(s, "MMM d")} – ${format(e, "MMM d, yyyy")}`;
  }

  return `${format(s, "MMM d, yyyy")} – ${format(e, "MMM d, yyyy")}`;
}
