export type SolutionPattern = {
  id: string;
  title: string;
  problem_category?: string | null;
  failure_mode?: string | null;
  root_cause_category?: string | null;
  symptom_tags: string[];
  recommended_actions: string[];
  actions_to_avoid: string[];
  evidence_summary?: string | null;
  effectiveness_rate?: number | null;
  usage_count: number;
  last_used_at?: string | null;
  created_from_plan_id?: string | null;
};

export type PagedSolutionPatternsResponse = {
  items: SolutionPattern[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};
