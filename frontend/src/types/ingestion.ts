export interface IngestRequest {
  url: string;
  attach_to_conference_id?: string | null;
}

export interface IngestResponse {
  conference_id: string | null;
  source_id: string;
  extraction_count: number;
  error: string | null;
}
