import { useMutation } from "@tanstack/react-query";
import { useQueryClient } from "@tanstack/react-query";
import { ingestionApi } from "@/api";
import { qk } from "@/utils/queryKeys";
import type { IngestRequest, IngestResponse } from "@/types";

export function useIngestUrl() {
  const qc = useQueryClient();

  return useMutation<IngestResponse, unknown, IngestRequest>({
    mutationFn: (data) => ingestionApi.ingestUrl(data),
    onSuccess: (result) => {
      // Invalidate conference lists so the newly created conference appears
      qc.invalidateQueries({ queryKey: qk.conferences.lists() });

      // If the ingestion was attached to an existing conference, refresh it
      if (result.conference_id) {
        qc.invalidateQueries({
          queryKey: qk.conferences.detail(result.conference_id),
        });
        qc.invalidateQueries({
          queryKey: qk.conferences.sources(result.conference_id),
        });
      }
    },
  });
}
