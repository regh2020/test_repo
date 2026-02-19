import { http } from "./client";
import type { DiscoveryQuery, DiscoveryRun, IngestResponse } from "@/types";

export const discoveryApi = {
  discover(query: DiscoveryQuery): Promise<DiscoveryRun> {
    return http.post<DiscoveryRun>("/discover", query).then((r) => r.data);
  },

  importCandidate(candidateUrl: string): Promise<IngestResponse> {
    return http
      .post<IngestResponse>("/import", { candidate_url: candidateUrl })
      .then((r) => r.data);
  },
};
