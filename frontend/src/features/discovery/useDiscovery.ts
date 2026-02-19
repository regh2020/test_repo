import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { discoveryApi, pendingDiscoveriesApi } from "@/api";
import { qk } from "@/utils/queryKeys";
import type { DiscoveryCandidate, DiscoveryQuery, DiscoveryRun, PendingDiscovery } from "@/types";

export function useDiscover() {
  return useMutation<DiscoveryRun, unknown, DiscoveryQuery>({
    mutationFn: (query) => discoveryApi.discover(query),
  });
}

/** Save a discovered candidate to the Pending Discoveries list (no AI extraction). */
export function useSaveToPending() {
  const qc = useQueryClient();
  return useMutation<PendingDiscovery, unknown, DiscoveryCandidate>({
    mutationFn: (candidate) =>
      discoveryApi.saveToPending({
        url: candidate.url,
        title: candidate.title,
        snippet: candidate.snippet,
        score: candidate.score,
        source_type: candidate.source_type,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.pendingDiscoveries.all });
    },
  });
}

export function usePendingDiscoveries() {
  return useQuery({
    queryKey: qk.pendingDiscoveries.all,
    queryFn: () => pendingDiscoveriesApi.list(),
  });
}

export function useImportPending() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => pendingDiscoveriesApi.import(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.pendingDiscoveries.all });
      qc.invalidateQueries({ queryKey: qk.conferences.lists() });
    },
  });
}

export function useDeletePending() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => pendingDiscoveriesApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.pendingDiscoveries.all });
    },
  });
}
