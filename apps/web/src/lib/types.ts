export type SourceTier = "mainstream" | "alternative" | "regional" | "community";

export interface Source {
  id: string;
  name: string;
  slug: string;
  url: string;
  rss_url: string | null;
  tier: SourceTier;
  department: string;
  scrape_strategy: string;
  description: string;
  is_active: boolean;
  last_scraped_at: string | null;
  total_articles_collected: number;
}

export interface Article {
  id: string;
  source_id: string;
  event_id: string | null;
  url: string;
  title: string;
  content: string;
  summary: string;
  published_at: string;
  scraped_at: string;
  department: string;
  category: string;
  entities: string[];
  source?: Source | null;
}

export interface StoryEvent {
  id: string;
  thread_id: string;
  title: string;
  summary: string;
  event_date: string;
  primary_department: string;
  category: string;
  entities: string[];
  mainstream_count: number;
  alternative_count: number;
  regional_count: number;
  community_count: number;
  is_blindspot: boolean;
  articles: Article[];
  thread_title?: string | null;
  thread_slug?: string | null;
}

export interface StoryThread {
  id: string;
  title: string;
  slug: string;
  current_summary: string;
  status: string;
  category: string;
  primary_department: string;
  departments_affected: string[];
  key_entities: string[];
  first_seen_at: string;
  last_updated_at: string;
  events_count: number;
  articles_count: number;
  mainstream_count: number;
  alternative_count: number;
  blindspot_ratio: number;
}

export interface StoryThreadDetail extends StoryThread {
  events: StoryEvent[];
}

export interface ScrapeRun {
  id: string;
  started_at: string;
  finished_at: string | null;
  trigger: string;
  status: string;
  sources_scanned: number;
  new_articles: number;
  new_events: number;
  updated_threads: number;
  details: Record<string, unknown>;
}

export interface DashboardOverview {
  total_threads: number;
  active_threads: number;
  total_events: number;
  total_articles: number;
  total_sources: number;
  blindspot_events_count: number;
  alternative_coverage_share: number;
  departments_summary: { department: string; articles_count: number }[];
  categories_summary: { category: string; threads_count: number }[];
  last_scrape: ScrapeRun | null;
}

export const BOLIVIA_DEPARTMENTS = [
  "All",
  "National",
  "La Paz",
  "Santa Cruz",
  "Cochabamba",
  "Potosí",
  "Oruro",
  "Tarija",
  "Chuquisaca",
  "Beni",
  "Pando",
] as const;

export const NEWS_CATEGORIES = [
  "All",
  "Justice & Public Security",
  "Politics & Governance",
  "Economy & Supply",
  "Social Conflicts & Labor",
  "Health & Public Services",
  "Environment & Territory",
  "Mining & Extractivism",
] as const;

export const TIER_LABELS: Record<SourceTier, string> = {
  alternative: "Independent / Investigative",
  community: "Community Radio / Agency",
  regional: "Regional / Departmental",
  mainstream: "Mainstream / Legacy",
};

export const SCRAPE_STRATEGY_LABELS: Record<string, string> = {
  rss: "RSS / XML Feed",
  html: "Web Portal (HTML)",
  youtube: "YouTube Broadcast",
  telegram: "Telegram Channel",
};
