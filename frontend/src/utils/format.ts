import type { ImportantDateType, ConferenceStatus } from "@/types";

export function formatImportantDateType(type: ImportantDateType): string {
  const labels: Record<ImportantDateType, string> = {
    submission_deadline: "Submission Deadline",
    abstract_submission_deadline: "Abstract Submission Deadline",
    notification_date: "Notification",
    camera_ready_deadline: "Camera Ready Deadline",
    conference_start_date: "Conference Start",
    conference_end_date: "Conference End",
    workshop_deadline: "Workshop Deadline",
    registration_deadline: "Registration Deadline",
    other: "Other",
  };
  return labels[type] ?? type;
}

export function formatStatus(status: ConferenceStatus): string {
  const labels: Record<ConferenceStatus, string> = {
    active: "Active",
    past: "Past",
    cancelled: "Cancelled",
    postponed: "Postponed",
  };
  return labels[status] ?? status;
}

/** Truncate a string to maxLen chars with ellipsis. */
export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen - 1) + "…";
}

/** Format a URL for display (strip protocol, trim trailing slash). */
export function displayUrl(url: string): string {
  return url.replace(/^https?:\/\//, "").replace(/\/$/, "");
}

/** Format confidence as a percentage string e.g. "87%" */
export function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}
