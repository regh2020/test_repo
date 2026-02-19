// ─── Enumerations ─────────────────────────────────────────────────────────────

export type ConferenceStatus =
  | "active"
  | "past"
  | "cancelled"
  | "postponed";

export type ImportantDateType =
  | "submission_deadline"
  | "abstract_submission_deadline"
  | "notification_date"
  | "camera_ready_deadline"
  | "conference_start_date"
  | "conference_end_date"
  | "workshop_deadline"
  | "registration_deadline"
  | "other";

export type SourceType = "website" | "cfp" | "twitter" | "rss";

export type ExtractionMethod = "heuristic" | "structured" | "manual";

// ─── Core domain models (mirrors backend read schemas) ────────────────────────

export interface Person {
  fullName: string;
  affiliation: string | null;
  role: string | null;
  personalUrl: string | null;
}

export interface Conference {
  id: string;
  name: string;
  acronym: string | null;
  series: string | null;
  topics: string[];
  city: string | null;
  country: string | null;
  venue: string | null;
  is_online: boolean;
  is_hybrid: boolean;
  start_date: string | null;
  end_date: string | null;
  cfp_url: string | null;
  website_url: string | null;
  status: ConferenceStatus;
  created_at: string;
  updated_at: string;
  submission_deadline: string | null;
  ai_summary: string | null;
  organizing_committee: Person[];
  scientific_committee: Person[];
}

export interface ImportantDate {
  id: string;
  conference_id: string;
  type: ImportantDateType;
  date_time: string;
  timezone: string | null;
  note: string | null;
  display_globally: boolean;
}

export interface Source {
  id: string;
  conference_id: string | null;
  type: SourceType;
  url: string;
  last_fetched_at: string | null;
  last_hash: string | null;
  fetch_status: string | null;
  refresh_interval_hours: number;
  refresh_enabled: boolean;
}

export interface ExtractionRecord {
  id: string;
  source_id: string;
  extracted_at: string;
  field_name: string;
  extracted_value: string;
  confidence: number;
  extraction_method: ExtractionMethod;
  raw_snippet: string | null;
}

// ─── Write schemas ────────────────────────────────────────────────────────────

export interface ConferenceCreate {
  name: string;
  acronym?: string | null;
  series?: string | null;
  topics?: string[];
  city?: string | null;
  country?: string | null;
  venue?: string | null;
  is_online?: boolean;
  is_hybrid?: boolean;
  start_date?: string | null;
  end_date?: string | null;
  cfp_url?: string | null;
  website_url?: string | null;
  status?: ConferenceStatus;
}

export type ConferenceUpdate = Partial<ConferenceCreate>;

export interface ImportantDateCreate {
  type: ImportantDateType;
  date_time: string;
  timezone?: string | null;
  note?: string | null;
  display_globally?: boolean;
}

export interface SourceCreate {
  type: SourceType;
  url: string;
  refresh_interval_hours?: number | null;
  refresh_enabled?: boolean;
}

// ─── List / filter params ─────────────────────────────────────────────────────

export interface ConferenceFilters {
  name?: string;
  acronym?: string;
  topic?: string;
  city?: string;
  country?: string;
  status?: ConferenceStatus;
  start_after?: string;
  start_before?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

export interface GlobalImportantDate {
  date: ImportantDate;
  conference: Conference;
}
