export interface RefreshRequest {
  conference_id?: string | null;
  force?: boolean;
}

export interface RefreshSourceResult {
  source_id: string;
  changed: boolean;
  new_record_count: number;
  error: string | null;
}

export interface RefreshResponse {
  results: RefreshSourceResult[];
}
