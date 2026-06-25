export type EvidenceSearchHit = {
  id: string;
  plan_id: string;
  type?: string;
  file_name?: string | null;
  stored_name?: string | null;
  description?: string | null;
  text_excerpt?: string | null;
  section?: string | null;
  plan_code?: string | null;
  plan_title?: string | null;
  branch_code?: string | null;
  product_code?: string | null;
  created_at?: string | null;
};

export type PagedEvidenceSearchResponse = {
  query: string;
  items: EvidenceSearchHit[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};
