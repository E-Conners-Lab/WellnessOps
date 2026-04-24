export interface APIResponse<T = unknown> {
  status: "success" | "error";
  data: T;
  meta?: PaginatedMeta;
}

export interface PaginatedMeta {
  page: number;
  per_page: number;
  total: number;
}

export interface ErrorResponse {
  status: "error";
  message: string;
  correlation_id?: string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface KnowledgeDocument {
  id: string;
  domain: string;
  title: string;
  source: string | null;
  file_type: string | null;
  tags: string[];
  chunk_count: number;
  chromadb_collection: string;
  ingested_at: string | null;
  ingestion_status: string;
  notes: string | null;
  created_at: string;
}

export interface DomainStats {
  domain: string;
  collection_name: string;
  description: string;
  document_count: number;
  total_chunks: number;
}

export interface SearchResult {
  id: string;
  text: string;
  metadata: Record<string, string>;
  distance: number | null;
  domain: string;
}

export interface Client {
  id: string;
  user_id: string;
  display_name: string;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  pii_consent: boolean;
  notes: string | null;
  budget_tier: string | null;
  has_wearable: boolean;
  wearable_type: string | null;
  financial_audit_consent: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuditSession {
  id: string;
  client_id: string;
  user_id: string;
  audit_tier: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  observations?: Observation[];
}

export interface Observation {
  id: string;
  session_id: string;
  room_area: string;
  category: string | null;
  observation_type: string;
  content: string | null;
  photo_path: string | null;
  photo_thumbnail_path: string | null;
  is_from_structured_flow: boolean;
  auto_categorized: boolean;
  domain_tags: string[] | null;
  sort_order: number;
  prompt_key: string | null;
  skipped: boolean;
  created_at: string;
  updated_at: string;
}

export interface SessionProgress {
  total_prompts: number;
  completed_prompts: number;
  skipped_prompts: number;
  completion_percent: number;
  sections: SectionProgress[];
}

export interface SectionProgress {
  room_area: string;
  label: string;
  total_prompts: number;
  completed_prompts: number;
  skipped_prompts: number;
}

export interface PromptDef {
  key: string;
  text: string;
  sort_order: number;
}

export interface RoomSection {
  room_area: string;
  label: string;
  tier: string;
  prompts: PromptDef[];
}

export const DOMAIN_LABELS: Record<string, string> = {
  well: "WELL Building Standard",
  research: "Articles & Research",
  products: "Product Recommendations",
  patterns: "Client Patterns",
  philosophies: "Lifestyle Philosophies",
  aesthetics: "Art & Aesthetics",
  partners: "Partners & Vendors",
};
