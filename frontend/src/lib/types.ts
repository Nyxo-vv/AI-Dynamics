export interface Article {
  id: number;
  title: string;
  title_zh: string | null;
  url: string;
  author?: string | null;
  content?: string | null;
  summary_zh: string | null;
  cover_image: string | null;
  images: string[];
  related_links: { label: string; url: string }[];
  language: string;
  published_at: string | null;
  fetched_at: string | null;
  importance: number;
  is_read: boolean;
  is_starred: boolean;
  source_name: string | null;
  tags: string[];
}

export interface Source {
  id: number;
  name: string;
  url: string;
  type: string;
  category: string;
  enabled: boolean;
  fetch_interval_min: number;
  last_fetched_at: string | null;
  created_at: string | null;
}

export interface BriefingHeadline {
  article_id: number;
  rank: number;
}

export interface BriefingSection {
  category: string;
  label: string;
  article_ids: number[];
}

export interface BriefingStats {
  total: number;
  headline_count: number;
  by_category: Record<string, number>;
  by_source: Record<string, number>;
}

export interface BriefingContent {
  headlines: BriefingHeadline[];
  sections: BriefingSection[];
  stats: BriefingStats;
}

export interface Briefing {
  id: number;
  date: string;
  window_start: string;
  window_end: string;
  content: BriefingContent;
  article_count: number;
  generated_at: string | null;
  articles: Record<number, Article>;
}

export interface BriefingStatus {
  date: string;
  generated: boolean;
  article_count: number;
  generated_at: string | null;
}

export interface FetchStatus {
  status: "idle" | "fetching" | "processing";
  total_sources: number;
  processed_sources: number;
  new_articles: number;
  llm_total: number;
  llm_processed: number;
}
