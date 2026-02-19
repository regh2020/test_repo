import { useMutation, useQueryClient } from "@tanstack/react-query";
import { refreshApi } from "@/api";
import { qk } from "@/utils/queryKeys";
import type { RefreshRequest, RefreshResponse, RefreshSourceResult } from "@/types";

export function useRefresh() {
  const qc = useQueryClient();

  return useMutation<RefreshResponse, unknown, RefreshRequest>({
    mutationFn: (data) => refreshApi.refresh(data),
    onSuccess: () => {
      // After refresh, conference data might have changed
      qc.invalidateQueries({ queryKey: qk.conferences.all });
    },
  });
}

export function useRefreshSource() {
  const qc = useQueryClient();

  return useMutation<RefreshSourceResult, unknown, string>({
    mutationFn: (sourceId) => refreshApi.refreshSource(sourceId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.conferences.all });
    },
  });
}

/** Refresh all sources for a specific conference. */
export function useRefreshConference() {
  const qc = useQueryClient();

  return useMutation<RefreshResponse, unknown, string>({
    mutationFn: (conferenceId) =>
      refreshApi.refresh({ conference_id: conferenceId }),
    onSuccess: (_data, conferenceId) => {
      qc.invalidateQueries({ queryKey: qk.conferences.detail(conferenceId) });
      qc.invalidateQueries({ queryKey: qk.conferences.sources(conferenceId) });
    },
  });
}
