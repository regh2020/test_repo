import { http } from "./client";
import type {
  Conference,
  ConferenceCreate,
  ConferenceFilters,
  ConferenceUpdate,
  ExtractionRecord,
  GlobalImportantDate,
  ImportantDate,
  ImportantDateCreate,
  PendingDiscovery,
  Source,
  SourceCreate,
} from "@/types";

// ─── Conferences ──────────────────────────────────────────────────────────────

export const conferencesApi = {
  list(filters: ConferenceFilters = {}): Promise<Conference[]> {
    const params: Record<string, string | number | undefined> = {};
    if (filters.name) params.name = filters.name;
    if (filters.acronym) params.acronym = filters.acronym;
    if (filters.topic) params.topic = filters.topic;
    if (filters.city) params.city = filters.city;
    if (filters.country) params.country = filters.country;
    if (filters.status) params.status = filters.status;
    if (filters.start_after) params.start_after = filters.start_after;
    if (filters.start_before) params.start_before = filters.start_before;
    if (filters.sort_by) params.sort_by = filters.sort_by;
    if (filters.sort_order) params.sort_order = filters.sort_order;
    params.limit = filters.limit ?? 100;
    params.offset = filters.offset ?? 0;

    return http
      .get<Conference[]>("/conferences", { params })
      .then((r) => r.data);
  },

  get(id: string): Promise<Conference> {
    return http.get<Conference>(`/conferences/${id}`).then((r) => r.data);
  },

  create(data: ConferenceCreate): Promise<Conference> {
    return http.post<Conference>("/conferences", data).then((r) => r.data);
  },

  update(id: string, data: ConferenceUpdate): Promise<Conference> {
    return http
      .patch<Conference>(`/conferences/${id}`, data)
      .then((r) => r.data);
  },

  delete(id: string): Promise<void> {
    return http.delete(`/conferences/${id}`).then(() => undefined);
  },

  // ─── Important dates ────────────────────────────────────────────────────────

  listDates(conferenceId: string): Promise<ImportantDate[]> {
    return http
      .get<ImportantDate[]>(`/conferences/${conferenceId}/dates`)
      .then((r) => r.data);
  },

  addDate(
    conferenceId: string,
    data: ImportantDateCreate
  ): Promise<ImportantDate> {
    return http
      .post<ImportantDate>(`/conferences/${conferenceId}/dates`, data)
      .then((r) => r.data);
  },

  deleteDate(dateId: string): Promise<void> {
    return http.delete(`/conferences/dates/${dateId}`).then(() => undefined);
  },

  updateDateDisplayGlobally(dateId: string, display_globally: boolean): Promise<ImportantDate> {
    return http
      .patch<ImportantDate>(`/conferences/dates/${dateId}/display-globally`, { display_globally })
      .then((r) => r.data);
  },

  listGlobalImportantDates(): Promise<GlobalImportantDate[]> {
    return http
      .get<GlobalImportantDate[]>("/important-dates")
      .then((r) => r.data);
  },

  // ─── Sources ────────────────────────────────────────────────────────────────

  listSources(conferenceId: string): Promise<Source[]> {
    return http
      .get<Source[]>(`/conferences/${conferenceId}/sources`)
      .then((r) => r.data);
  },

  addSource(conferenceId: string, data: SourceCreate): Promise<Source> {
    return http
      .post<Source>(`/conferences/${conferenceId}/sources`, data)
      .then((r) => r.data);
  },

  // ─── Extraction records (provenance) ────────────────────────────────────────

  listExtractions(sourceId: string): Promise<ExtractionRecord[]> {
    return http
      .get<ExtractionRecord[]>(`/sources/${sourceId}/extractions`)
      .then((r) => r.data);
  },
};

// ─── Pending Discoveries ──────────────────────────────────────────────────────

export const pendingDiscoveriesApi = {
  list(): Promise<PendingDiscovery[]> {
    return http.get<PendingDiscovery[]>("/pending-discoveries").then((r) => r.data);
  },

  add(data: { url: string; title?: string | null; snippet?: string | null; score?: number; source_type?: string }): Promise<PendingDiscovery> {
    return http.post<PendingDiscovery>("/pending-discoveries", data).then((r) => r.data);
  },

  delete(id: string): Promise<void> {
    return http.delete(`/pending-discoveries/${id}`).then(() => undefined);
  },

  import(id: string): Promise<{ conference_id: string | null; source_id: string; extraction_count: number; error: string | null }> {
    return http.post(`/pending-discoveries/${id}/import`).then((r) => r.data);
  },
};
