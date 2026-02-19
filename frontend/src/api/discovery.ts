import { http } from "./client";
import type { DiscoveryQuery, DiscoveryRun, PendingDiscovery } from "@/types";

export const discoveryApi = {
  discover(query: DiscoveryQuery): Promise<DiscoveryRun> {
    return http.post<DiscoveryRun>("/discover", query).then((r) => r.data);
  },

  /** Save a discovered candidate URL to the Pending Discoveries list (no AI extraction). */
  saveToPending(candidate: { url: string; title?: string | null; snippet?: string | null; score?: number; source_type?: string }): Promise<PendingDiscovery> {
    return http
      .post<PendingDiscovery>("/import", candidate)
      .then((r) => r.data);
  },
};
