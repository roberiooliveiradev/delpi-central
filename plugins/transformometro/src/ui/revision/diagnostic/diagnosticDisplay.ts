/**
 * Presentation labels for the canonical Diagnostic contract (pt-BR UI).
 * Values stay canonical in payloads — these are display-only mappings.
 */
import type {
  DiagnosticClaimLifecycle,
  DiagnosticEffectiveValidation,
  DiagnosticEpistemicState,
  DiagnosticEvidenceRelation,
  DiagnosticManageAction,
} from "../../../data/api/transformometroDiagnosticApi";

export const EPISTEMIC_LABELS: Record<DiagnosticEpistemicState, string> = {
  OBSERVED: "Observado",
  CALCULATED: "Calculado",
  INFERRED: "Inferido",
  PROPOSED: "Proposto",
  UNKNOWN: "Não identificado",
};

export const EPISTEMIC_HELP: Record<DiagnosticEpistemicState, string> = {
  OBSERVED: "Achado observado diretamente na operação ou nos dados.",
  CALCULATED: "Valor derivado de cálculo sobre dados — não é um fato observado.",
  INFERRED: "Interpretação — não é fato, mesmo quando validada.",
  PROPOSED: "Registro proposto, ainda sem respaldo definido.",
  UNKNOWN: "Natureza epistêmica não determinada.",
};

export const LIFECYCLE_LABELS: Record<DiagnosticClaimLifecycle, string> = {
  DRAFT: "Rascunho",
  VALIDATED: "Validada",
  REJECTED: "Rejeitada",
  SUPERSEDED: "Substituída",
};

export const EFFECTIVE_VALIDATION_LABELS: Record<DiagnosticEffectiveValidation, string> = {
  CURRENT: "Atual",
  STALE_EVIDENCE: "Evidência desatualizada",
  REVALIDATION_REQUIRED: "Requer revalidação",
};

export const EFFECTIVE_VALIDATION_HELP: Record<DiagnosticEffectiveValidation, string> = {
  CURRENT: "Diagnóstico compatível com as evidências consideradas.",
  STALE_EVIDENCE: "Há evidências mais recentes que ainda não foram consideradas.",
  REVALIDATION_REQUIRED: "O diagnóstico precisa ser revisado antes de ser considerado atualizado.",
};

export const EVIDENCE_RELATION_LABELS: Record<DiagnosticEvidenceRelation, string> = {
  SUPPORTS: "Sustenta",
  CONTRADICTS: "Contradiz",
  CONTEXTUALIZES: "Contextualiza",
};

/** Única relação causal do V1 — nunca "causa"/"prova". */
export const CAUSAL_RELATION_LABEL = "contribui para";

export const FINDING_ROLE_LABELS: Record<string, string> = {
  SYMPTOM: "Sintoma",
};

export const PROVENANCE_ORIGIN_LABELS: Record<string, string> = {
  USER: "Registrado no portal",
  TEO: "Registrado pelo TÉO",
};

export const DIAGNOSTIC_ACTION_LABELS: Record<DiagnosticManageAction, string> = {
  add_finding: "Adicionar achado",
  add_hypothesis: "Adicionar hipótese",
  add_causal_link: "Adicionar relação causal",
  add_evidence_link: "Vincular evidência existente",
  add_conclusion: "Adicionar conclusão",
  validate_hypothesis: "Validar hipótese",
  reject_hypothesis: "Rejeitar hipótese",
  supersede_hypothesis: "Substituir hipótese",
  mark_hypothesis_stale_evidence: "Marcar evidência desatualizada",
  mark_hypothesis_revalidation_required: "Marcar para revalidação",
  validate_conclusion: "Validar conclusão",
  reject_conclusion: "Rejeitar conclusão",
  supersede_conclusion: "Substituir conclusão",
};

/** Field labels for the sealed exact_change payload shown in the review. */
export const EXACT_CHANGE_FIELD_LABELS: Record<string, string> = {
  statement: "Enunciado",
  problem_statement: "Problema investigado",
  role: "Papel",
  epistemic_state: "Natureza epistêmica",
  provenance: "Origem",
  evidence_id: "Evidência",
  relation: "Relação",
  target_id: "Destino",
  source_hypothesis_id: "Hipótese de origem",
  hypothesis_id: "Hipótese",
  conclusion_id: "Conclusão",
  finding_id: "Achado",
  link_id: "Vínculo",
  diagnostic_id: "Diagnóstico",
  revision_id: "Revisão",
  expected_version: "Versão esperada",
  action: "Ação",
  note: "Nota",
  rationale: "Justificativa",
  hypothesis_ids: "Hipóteses referenciadas",
  finding_ids: "Achados referenciados",
  root_cause_hypothesis_id: "Hipótese causa-raiz",
  origin: "Origem",
  detail: "Detalhe",
};

export function epistemicLabel(value: string | null | undefined): string {
  return EPISTEMIC_LABELS[value as DiagnosticEpistemicState] ?? value ?? "—";
}

export function lifecycleLabel(value: string | null | undefined): string {
  return LIFECYCLE_LABELS[value as DiagnosticClaimLifecycle] ?? value ?? "—";
}

export function effectiveValidationLabel(value: string | null | undefined): string {
  return EFFECTIVE_VALIDATION_LABELS[value as DiagnosticEffectiveValidation] ?? value ?? "—";
}

export function evidenceRelationLabel(value: string | null | undefined): string {
  return EVIDENCE_RELATION_LABELS[value as DiagnosticEvidenceRelation] ?? value ?? "—";
}
