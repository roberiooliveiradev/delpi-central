export type SimilarCaseItem = {
  plan_id: string;
  plan_uuid?: string;
  similarity_score: number;
  product_code?: string;
  problem_summary?: string;
  root_cause?: string;
  effective_actions?: string[];
  effectiveness_status?: string;
  closed_at?: string;
};

export type PlanSimilarCasesResult = {
  similar_cases: SimilarCaseItem[];
  recurrence_signals: {
    same_product: number;
    same_symptom: number;
    same_root_cause_category: number;
  };
  suggested_focus_areas: string[];
};
