export * from "./conference";
export * from "./discovery";
export * from "./ingestion";
export * from "./refresh";

// ─── Shared utility types ─────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
  status: number;
}

export interface PaginationState {
  page: number;
  pageSize: number;
}
