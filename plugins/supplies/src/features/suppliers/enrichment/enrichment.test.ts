import { describe, expect, it } from "vitest";

import {
  COMPARISON_LABELS,
  COMPARISON_VARIANTS,
  DECISION_LABELS,
  ELIGIBILITY_LABELS,
  ENRICHMENT_CONTENT,
  REVIEW_STATUS_LABELS,
  mapEnrichmentError,
} from "./content";
import {
  bulkAcceptAllowed,
  canAcceptProposal,
  canRejectProposal,
  enrichmentFieldLabel,
  isReviewActionable,
  newIdempotencyKey,
  pickActiveReview,
  selectableFieldKeys,
  summarizeProposals,
} from "./stateMachine";
import type {
  ComparisonState,
  DecisionState,
  EligibilityState,
  EnrichmentProposal,
  EnrichmentReview,
  EnrichmentReviewStatus,
} from "./types";

function proposal(overrides: Partial<EnrichmentProposal> = {}): EnrichmentProposal {
  return {
    proposal_id: "p-1",
    field_key: "supplier_name",
    section_key: "identification",
    comparison_state: "DIFFERENT",
    eligibility_state: "ELIGIBLE_TO_APPLY",
    eligibility_reason: null,
    source_field: "company.legal_name",
    source_reference: null,
    current_value: "ANTIGA",
    suggested_value: "NOVA",
    decision_state: "PENDING",
    ...overrides,
  };
}

function review(status: EnrichmentReviewStatus): EnrichmentReview {
  return {
    review_id: "r-1",
    supplier_code: "002469",
    supplier_store: "01",
    status,
    revision: 1,
    actor_subject: "sub",
    source_id: "brasilapi-cnpj-v1",
    source_reference: null,
    source_retrieved_at: "2026-10-22T14:00:00+00:00",
    mapping_version: "cnpj-sa2-v1",
    normalization_version: "norm-v1",
    created_at: "2026-10-22T14:00:00+00:00",
    updated_at: "2026-10-22T14:00:00+00:00",
    expires_at: "2026-10-23T14:00:00+00:00",
  };
}

describe("enrichment field labels", () => {
  it("uses the shared registry label for cadastral keys", () => {
    expect(enrichmentFieldLabel("supplier_name")).toBe("Razão social");
    expect(enrichmentFieldLabel("postal_code")).toBe("CEP");
  });

  it("falls back to the raw key for information-only fields", () => {
    expect(enrichmentFieldLabel("main_cnae")).toBe("main_cnae");
  });
});

describe("decision gates (contract-faithful)", () => {
  it("accept requires PENDING + ELIGIBLE_TO_APPLY", () => {
    expect(canAcceptProposal(proposal())).toBe(true);
    expect(
      canAcceptProposal(proposal({ eligibility_state: "PROTECTED" })),
    ).toBe(false);
    expect(
      canAcceptProposal(
        proposal({ eligibility_state: "PENDING_VALIDATION" }),
      ),
    ).toBe(false);
    expect(
      canAcceptProposal(proposal({ decision_state: "ACCEPTED_FOR_DRAFT" })),
    ).toBe(false);
  });

  it("reject is allowed for any pending proposal", () => {
    expect(canRejectProposal(proposal())).toBe(true);
    expect(
      canRejectProposal(proposal({ eligibility_state: "PROTECTED" })),
    ).toBe(true);
    expect(
      canRejectProposal(proposal({ decision_state: "REJECTED_SUGGESTION" })),
    ).toBe(false);
  });

  it("review is actionable only in IN_REVIEW/DECIDED", () => {
    expect(isReviewActionable(review("IN_REVIEW"))).toBe(true);
    expect(isReviewActionable(review("DECIDED"))).toBe(true);
    expect(isReviewActionable(review("EXPIRED"))).toBe(false);
    expect(isReviewActionable(review("STALE"))).toBe(false);
    expect(isReviewActionable(review("CANCELLED"))).toBe(false);
  });
});

describe("summary and bulk gates", () => {
  const proposals = [
    proposal({ field_key: "supplier_name" }),
    proposal({
      field_key: "district",
      comparison_state: "MATCH",
      decision_state: "PENDING",
    }),
    proposal({
      field_key: "phone",
      comparison_state: "SOURCE_MISSING",
      eligibility_state: "PENDING_VALIDATION",
    }),
    proposal({
      field_key: "tax_id",
      comparison_state: "PROTECTED",
      eligibility_state: "PROTECTED",
      decision_state: "PENDING",
    }),
    proposal({
      field_key: "email",
      comparison_state: "DIFFERENT",
      decision_state: "ACCEPTED_FOR_DRAFT",
    }),
  ];

  it("counts comparison and decision states", () => {
    const s = summarizeProposals(proposals);
    expect(s.different).toBe(2);
    expect(s.match).toBe(1);
    expect(s.other).toBe(2);
    expect(s.pending).toBe(4);
    expect(s.accepted).toBe(1);
    expect(s.rejected).toBe(0);
    expect(s.eligiblePending).toBe(2);
  });

  it("selectable = pending only", () => {
    expect(selectableFieldKeys(proposals).sort()).toEqual([
      "district",
      "phone",
      "supplier_name",
      "tax_id",
    ]);
  });

  it("bulk accept requires all selected to be eligible (atomic 422)", () => {
    expect(
      bulkAcceptAllowed(proposals, new Set(["supplier_name"])),
    ).toBe(true);
    // mixed selection inclui inelegível → bloqueado
    expect(
      bulkAcceptAllowed(proposals, new Set(["supplier_name", "phone"])),
    ).toBe(false);
    expect(bulkAcceptAllowed(proposals, new Set())).toBe(false);
  });

  it("picks the first actionable review from history", () => {
    const items = [review("EXPIRED"), review("IN_REVIEW")];
    expect(pickActiveReview(items)?.status).toBe("IN_REVIEW");
    expect(pickActiveReview([review("EXPIRED")])).toBeUndefined();
  });
});

describe("idempotency keys", () => {
  it("generates unique non-empty keys", () => {
    const a = newIdempotencyKey();
    const b = newIdempotencyKey();
    expect(a).toBeTruthy();
    expect(b).toBeTruthy();
    expect(a).not.toBe(b);
    expect(a.length).toBeLessThanOrEqual(128);
  });
});

describe("error mapping — real BFF codes", () => {
  it.each([
    ["ENRICHMENT_UNSUPPORTED_DOCUMENT", "errorUnsupportedDocument"],
    ["ENRICHMENT_REGISTRY_TAX_ID_NOT_FOUND", "errorTaxIdNotFound"],
    ["ENRICHMENT_REGISTRY_INVALID_TAX_ID", "errorInvalidTaxId"],
    ["ENRICHMENT_REGISTRY_INVALID_RESPONSE", "errorInvalidResponse"],
    ["ENRICHMENT_SOURCE_UNAVAILABLE", "errorSourceUnavailable"],
    ["ENRICHMENT_RATE_LIMITER_UNAVAILABLE", "errorSourceUnavailable"],
    ["ENRICHMENT_RATE_LIMITED", "errorRateLimited"],
    ["ENRICHMENT_REVIEW_EXPIRED", "errorReviewExpired"],
    ["ENRICHMENT_STALE_BASELINE", "errorStaleBaseline"],
    ["ENRICHMENT_REVISION_CONFLICT", "errorRevisionConflict"],
    ["ENRICHMENT_IDEMPOTENCY_CONFLICT", "errorIdempotencyConflict"],
    ["ENRICHMENT_PROPOSAL_ALREADY_DECIDED", "errorAlreadyDecided"],
    ["ENRICHMENT_PROPOSAL_NOT_ELIGIBLE", "errorNotEligible"],
    ["ENRICHMENT_REVIEW_CANCELLED", "errorCancelled"],
    ["forbidden", "errorForbidden"],
    ["not_found", "errorNotFound"],
  ])("maps code %s → %s", (code, contentKey) => {
    expect(mapEnrichmentError(undefined, code)).toBe(
      ENRICHMENT_CONTENT[contentKey as keyof typeof ENRICHMENT_CONTENT],
    );
  });

  it("falls back by status and never invents permissions", () => {
    expect(mapEnrichmentError(403)).toBe(ENRICHMENT_CONTENT.errorForbidden);
    expect(mapEnrichmentError(404)).toBe(ENRICHMENT_CONTENT.errorNotFound);
    expect(mapEnrichmentError(429)).toBe(ENRICHMENT_CONTENT.errorRateLimited);
    expect(mapEnrichmentError(503)).toBe(
      ENRICHMENT_CONTENT.errorSourceUnavailable,
    );
    expect(mapEnrichmentError(500)).toBe(ENRICHMENT_CONTENT.errorGeneric);
  });
});

describe("label maps cover every contract value", () => {
  const comparisons: ComparisonState[] = [
    "MATCH",
    "DIFFERENT",
    "SOURCE_MISSING",
    "CURRENT_MISSING",
    "NOT_COMPARABLE",
    "PROTECTED",
    "UNSUPPORTED",
    "ERROR",
  ];
  const eligibilities: EligibilityState[] = [
    "ELIGIBLE_TO_APPLY",
    "PROTECTED",
    "NOT_APPLICABLE",
    "PENDING_VALIDATION",
  ];
  const decisions: DecisionState[] = [
    "PENDING",
    "ACCEPTED_FOR_DRAFT",
    "REJECTED_SUGGESTION",
  ];
  const statuses: EnrichmentReviewStatus[] = [
    "IN_REVIEW",
    "DECIDED",
    "EXPIRED",
    "STALE",
    "CANCELLED",
  ];

  it("every enum has label and variant", () => {
    for (const c of comparisons) {
      expect(COMPARISON_LABELS[c]).toBeTruthy();
      expect(COMPARISON_VARIANTS[c]).toBeTruthy();
    }
    for (const e of eligibilities) expect(ELIGIBILITY_LABELS[e]).toBeTruthy();
    for (const d of decisions) expect(DECISION_LABELS[d]).toBeTruthy();
    for (const s of statuses) expect(REVIEW_STATUS_LABELS[s]).toBeTruthy();
  });
});
