import { SUPPLIER_FIELD_REGISTRY } from "../types";
import type {
  EnrichmentProposal,
  EnrichmentReview,
  EnrichmentReviewStatus,
} from "./types";

/** Rótulo do campo: registry cadastral primeiro; chave crua como fallback. */
export function enrichmentFieldLabel(fieldKey: string): string {
  return (
    SUPPLIER_FIELD_REGISTRY.find((f) => f.key === fieldKey)?.label ?? fieldKey
  );
}

const ACTIONABLE_STATUSES: ReadonlySet<EnrichmentReviewStatus> = new Set([
  "IN_REVIEW",
  "DECIDED",
]);

/** O backend (_ACTIONABLE) aceita decisões/prepare em IN_REVIEW e DECIDED. */
export function isReviewActionable(review: EnrichmentReview): boolean {
  return ACTIONABLE_STATUSES.has(review.status);
}

export function canAcceptProposal(proposal: EnrichmentProposal): boolean {
  return (
    proposal.decision_state === "PENDING" &&
    proposal.eligibility_state === "ELIGIBLE_TO_APPLY"
  );
}

/** Rejeição é permitida para qualquer proposta pendente (contrato S2). */
export function canRejectProposal(proposal: EnrichmentProposal): boolean {
  return proposal.decision_state === "PENDING";
}

export type ReviewSummary = {
  different: number;
  match: number;
  other: number;
  pending: number;
  accepted: number;
  rejected: number;
  eligiblePending: number;
};

export function summarizeProposals(
  proposals: readonly EnrichmentProposal[],
): ReviewSummary {
  const summary: ReviewSummary = {
    different: 0,
    match: 0,
    other: 0,
    pending: 0,
    accepted: 0,
    rejected: 0,
    eligiblePending: 0,
  };
  for (const p of proposals) {
    if (p.comparison_state === "DIFFERENT") summary.different += 1;
    else if (p.comparison_state === "MATCH") summary.match += 1;
    else summary.other += 1;
    if (p.decision_state === "PENDING") summary.pending += 1;
    else if (p.decision_state === "ACCEPTED_FOR_DRAFT") summary.accepted += 1;
    else if (p.decision_state === "REJECTED_SUGGESTION") summary.rejected += 1;
    if (canAcceptProposal(p)) summary.eligiblePending += 1;
  }
  return summary;
}

/** Selecionável em lote: somente propostas pendentes. */
export function selectableFieldKeys(
  proposals: readonly EnrichmentProposal[],
): string[] {
  return proposals.filter(canRejectProposal).map((p) => p.field_key);
}

/**
 * Aceite em lote só é seguro quando toda a seleção é elegível — o bulk é
 * atômico e um campo inelegível rejeita a operação inteira (422).
 */
export function bulkAcceptAllowed(
  proposals: readonly EnrichmentProposal[],
  selected: ReadonlySet<string>,
): boolean {
  if (!selected.size) return false;
  return proposals
    .filter((p) => selected.has(p.field_key))
    .every((p) => canAcceptProposal(p));
}

/**
 * Chave idempotente estável por tentativa de ação: o caller guarda a chave
 * enquanto a operação estiver em voo e a reusa somente em retry da MESMA
 * operação (mesmo payload). Operação semanticamente nova = nova chave.
 */
export function newIdempotencyKey(): string {
  if (
    typeof globalThis.crypto !== "undefined" &&
    typeof globalThis.crypto.randomUUID === "function"
  ) {
    return globalThis.crypto.randomUUID();
  }
  return `op-${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;
}

/** Revisão mais recente ainda acionável — auto-seleção após listar. */
export function pickActiveReview(
  items: readonly EnrichmentReview[],
): EnrichmentReview | undefined {
  return items.find((r) => isReviewActionable(r));
}
