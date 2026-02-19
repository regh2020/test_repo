import { http } from "./client";
import type { RefreshRequest, RefreshResponse, RefreshSourceResult } from "@/types";

export const refreshApi = {
  refresh(data: RefreshRequest = {}): Promise<RefreshResponse> {
    return http.post<RefreshResponse>("/refresh", data).then((r) => r.data);
  },

  refreshSource(sourceId: string): Promise<RefreshSourceResult> {
    return http
      .post<RefreshSourceResult>(`/sources/${sourceId}/refresh`)
      .then((r) => r.data);
  },
};
