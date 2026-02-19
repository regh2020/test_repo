import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { conferencesApi } from "@/api";
import { qk } from "@/utils/queryKeys";
import type {
  ConferenceCreate,
  ConferenceFilters,
  ConferenceUpdate,
  ImportantDateCreate,
  SourceCreate,
} from "@/types";

// ─── Queries ──────────────────────────────────────────────────────────────────

export function useConferences(filters: ConferenceFilters = {}) {
  return useQuery({
    queryKey: qk.conferences.list(filters),
    queryFn: () => conferencesApi.list(filters),
  });
}

export function useConference(id: string) {
  return useQuery({
    queryKey: qk.conferences.detail(id),
    queryFn: () => conferencesApi.get(id),
    enabled: Boolean(id),
  });
}

export function useConferenceDates(conferenceId: string) {
  return useQuery({
    queryKey: qk.conferences.dates(conferenceId),
    queryFn: () => conferencesApi.listDates(conferenceId),
    enabled: Boolean(conferenceId),
  });
}

export function useConferenceSources(conferenceId: string) {
  return useQuery({
    queryKey: qk.conferences.sources(conferenceId),
    queryFn: () => conferencesApi.listSources(conferenceId),
    enabled: Boolean(conferenceId),
  });
}

// ─── Mutations ────────────────────────────────────────────────────────────────

export function useCreateConference() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ConferenceCreate) => conferencesApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.conferences.lists() });
    },
  });
}

export function useUpdateConference(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ConferenceUpdate) => conferencesApi.update(id, data),
    onSuccess: (updated) => {
      qc.setQueryData(qk.conferences.detail(id), updated);
      qc.invalidateQueries({ queryKey: qk.conferences.lists() });
    },
  });
}

export function useDeleteConference() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => conferencesApi.delete(id),
    onSuccess: (_data, id) => {
      qc.removeQueries({ queryKey: qk.conferences.detail(id) });
      qc.invalidateQueries({ queryKey: qk.conferences.lists() });
    },
  });
}

export function useAddDate(conferenceId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ImportantDateCreate) =>
      conferencesApi.addDate(conferenceId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.conferences.dates(conferenceId) });
    },
  });
}

export function useDeleteDate(conferenceId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (dateId: string) => conferencesApi.deleteDate(dateId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.conferences.dates(conferenceId) });
    },
  });
}

export function useAddSource(conferenceId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SourceCreate) =>
      conferencesApi.addSource(conferenceId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.conferences.sources(conferenceId) });
    },
  });
}
