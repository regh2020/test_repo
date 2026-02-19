import { http } from "./client";
import type { IngestRequest, IngestResponse } from "@/types";

export const ingestionApi = {
  ingestUrl(data: IngestRequest): Promise<IngestResponse> {
    return http
      .post<IngestResponse>("/ingest/url", data)
      .then((r) => r.data);
  },
};
