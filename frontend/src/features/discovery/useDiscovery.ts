import { useMutation, useQueryClient } from "@tanstack/react-query";
import { discoveryApi } from "@/api";
import { qk } from "@/utils/queryKeys";
import type { DiscoveryQuery, DiscoveryRun } from "@/types";

export function useDiscover() {
  return useMutation<DiscoveryRun, unknown, DiscoveryQuery>({
    mutationFn: (query) => discoveryApi.discover(query),
  });
}

export function useImportCandidate() {
  const qc = useQueryClient();

  return useMutation<
    Awaited<ReturnType<typeof discoveryApi.importCandidate>>,
    unknown,
    string
  >({
    mutationFn: (url) => discoveryApi.importCandidate(url),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.conferences.lists() });
    },
  });
}
