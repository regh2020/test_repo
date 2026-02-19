export interface DiscoveryQuery {
  keywords?: string[];
  topics?: string[];
  date_range_start?: string | null;
  date_range_end?: string | null;
  include_twitter?: boolean;
}

export interface DiscoveryCandidate {
  url: string;
  title: string | null;
  snippet: string | null;
  score: number;
  source_type: string;
}

export interface DiscoveryRun {
  id: string;
  query: string;
  started_at: string;
  finished_at: string | null;
  candidates: DiscoveryCandidate[];
}
