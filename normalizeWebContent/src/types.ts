export interface ZendeskArticle {
  id: number;
  url: string;
  html_url: string;
  author_id: number;
  comments_disabled: boolean;
  draft: boolean;
  promoted: boolean;
  position: number;
  vote_sum: number;
  vote_count: number;
  section_id: number;
  created_at: string;
  updated_at: string;
  name: string;
  title: string;
  source_locale: string;
  locale: string;
  outdated: boolean;
  outdated_locales: string[];
  edited_at: string;
  user_segment_id: number | null;
  permission_group_id: number;
  content_tag_ids: number[];
  label_names: string[];
  body: string;
}

export interface ZendeskSection {
  id: number;
  url: string;
  html_url: string;
  category_id: number;
  position: number;
  sorting: string;
  created_at: string;
  updated_at: string;
  name: string;
  description: string;
  locale: string;
  source_locale: string;
  outdated: boolean;
  theme_template: string;
  parent_section_id: number | null;
}

export interface ZendeskCategory {
  id: number;
  url: string;
  html_url: string;
  position: number;
  created_at: string;
  updated_at: string;
  name: string;
  description: string;
  locale: string;
  source_locale: string;
  outdated: boolean;
}

export interface ZendeskApiResponse<T> {
  [key: string]: T[] | number | string | null;
  page: number;
  per_page: number;
  page_count: number;
  count: number;
  next_page: string | null;
  previous_page: string | null;
}

export interface ScrapingConfig {
  baseUrl: string;
  outputDir: string;
  maxArticles?: number;
  delay?: number;
  retries?: number;
}

export interface ProcessedArticle {
  id: number;
  title: string;
  slug: string;
  content: string;
  url: string;
  category: string;
  section: string;
  createdAt: string;
  updatedAt: string;
}
