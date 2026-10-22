/**
 * DTOs do contrato de enriquecimento cadastral (supplies-api S2).
 * Espelham `_review_view`, `_proposal_view`, `_decision_view` e o envelope
 * de `prepare-update` em `supplier_enrichment_routes.py` — nunca estender
 * com campos que o backend não publica.
 */

export type ComparisonState =
  | "MATCH"
  | "DIFFERENT"
  | "SOURCE_MISSING"
  | "CURRENT_MISSING"
  | "NOT_COMPARABLE"
  | "PROTECTED"
  | "UNSUPPORTED"
  | "ERROR";

export type EligibilityState =
  | "ELIGIBLE_TO_APPLY"
  | "PROTECTED"
  | "NOT_APPLICABLE"
  | "PENDING_VALIDATION";

export type DecisionState =
  | "PENDING"
  | "ACCEPTED_FOR_DRAFT"
  | "REJECTED_SUGGESTION";

export type EnrichmentReviewStatus =
  | "IN_REVIEW"
  | "DECIDED"
  | "EXPIRED"
  | "STALE"
  | "CANCELLED";

export type EnrichmentReview = {
  review_id: string;
  supplier_code: string;
  supplier_store: string;
  status: EnrichmentReviewStatus;
  revision: number;
  actor_subject: string;
  source_id: string;
  source_reference: string | null;
  source_retrieved_at: string | null;
  mapping_version: string;
  normalization_version: string;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
};

export type EnrichmentProposal = {
  proposal_id: string;
  field_key: string;
  section_key: string;
  comparison_state: ComparisonState;
  eligibility_state: EligibilityState;
  eligibility_reason: string | null;
  source_field: string | null;
  source_reference: string | null;
  current_value: string | null;
  suggested_value: string | null;
  decision_state: DecisionState;
};

export type EnrichmentDecision = {
  decision_id: string;
  proposal_id: string;
  operation_id: string;
  field_key: string;
  actor_subject: string;
  decision: "ACCEPT" | "REJECT";
  reason_code: string | null;
  decided_at: string;
  review_revision: number;
};

export type EnrichmentReviewListEnvelope = {
  items?: EnrichmentReview[];
  page?: number;
  page_size?: number;
  total?: number;
};

export type EnrichmentDecisionListEnvelope = {
  items?: EnrichmentDecision[];
};

export type EnrichmentReviewPayload = {
  review: EnrichmentReview;
  proposals: EnrichmentProposal[];
};

export type EnrichmentDecisionPayload = EnrichmentReviewPayload & {
  idempotent_replay: boolean;
};

export type EnrichmentDraftField = {
  field_key: string;
  current_value: string | null;
  proposed_value: string | null;
  proposal_id: string;
  decision_id: string;
};

export type EnrichmentPrepareUpdateResult = {
  review_id: string;
  revision: number;
  supplier: { supplier_code: string; supplier_store: string };
  baseline_status: string;
  write_gate_enabled: boolean;
  draft_fields: EnrichmentDraftField[];
};
