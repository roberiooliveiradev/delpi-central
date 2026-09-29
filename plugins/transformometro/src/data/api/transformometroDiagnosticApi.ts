/**
 * Diagnostic — canonical Portal HTTP client (Backend 1/3 contract).
 *
 * Transport DTOs mirror `tm_app/interface/diagnostic_projection.py`; the
 * action allowlist mirrors `MANAGE_ACTIONS` in
 * `tm_app/application/governed_writes/diagnostic_capabilities.py`. This
 * module is an adapter only — no domain semantics, no client-side ids, no
 * writes outside PREPARE → explicit confirmation → COMMIT.
 */
import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "./transformometroApiBase";
import { parseApiEnvelope } from "./transformometroHttp";

// ---------------------------------------------------------------------------
// Canonical enums (values are contract, labels live in diagnosticDisplay.ts)
// ---------------------------------------------------------------------------

export type DiagnosticEpistemicState =
  | "OBSERVED"
  | "CALCULATED"
  | "INFERRED"
  | "PROPOSED"
  | "UNKNOWN";

export type DiagnosticClaimLifecycle =
  | "DRAFT"
  | "VALIDATED"
  | "REJECTED"
  | "SUPERSEDED";

export type DiagnosticEvidenceRelation =
  | "SUPPORTS"
  | "CONTRADICTS"
  | "CONTEXTUALIZES";

export type DiagnosticEffectiveValidation =
  | "CURRENT"
  | "STALE_EVIDENCE"
  | "REVALIDATION_REQUIRED";

export type DiagnosticCausalRelation = "CONTRIBUTES_TO";

export type DiagnosticFindingRole = "SYMPTOM";

export type DiagnosticProvenance = {
  origin: string;
  detail?: string | null;
} | null;

// ---------------------------------------------------------------------------
// Canonical material actions — exactly the backend-proven MANAGE_ACTIONS.
// ---------------------------------------------------------------------------

export const DIAGNOSTIC_ENTITY_ACTIONS = [
  "add_finding",
  "add_hypothesis",
  "add_causal_link",
  "add_evidence_link",
  "add_conclusion",
] as const;

export const DIAGNOSTIC_HYPOTHESIS_LIFECYCLE_ACTIONS = [
  "validate_hypothesis",
  "reject_hypothesis",
  "supersede_hypothesis",
] as const;

export const DIAGNOSTIC_HYPOTHESIS_MARK_ACTIONS = [
  "mark_hypothesis_stale_evidence",
  "mark_hypothesis_revalidation_required",
] as const;

export const DIAGNOSTIC_CONCLUSION_LIFECYCLE_ACTIONS = [
  "validate_conclusion",
  "reject_conclusion",
  "supersede_conclusion",
] as const;

/** Exact backend allowlist (MANAGE_ACTIONS) — 13 actions, no more, no less. */
export const DIAGNOSTIC_ACTION_ALLOWLIST = [
  ...DIAGNOSTIC_ENTITY_ACTIONS,
  ...DIAGNOSTIC_HYPOTHESIS_LIFECYCLE_ACTIONS,
  ...DIAGNOSTIC_HYPOTHESIS_MARK_ACTIONS,
  ...DIAGNOSTIC_CONCLUSION_LIFECYCLE_ACTIONS,
] as const;

export type DiagnosticManageAction = (typeof DIAGNOSTIC_ACTION_ALLOWLIST)[number];

export function isDiagnosticManageAction(value: string): value is DiagnosticManageAction {
  return (DIAGNOSTIC_ACTION_ALLOWLIST as readonly string[]).includes(value);
}

// ---------------------------------------------------------------------------
// Transport DTOs (read model — projection shape, not a frontend domain model)
// ---------------------------------------------------------------------------

export type DiagnosticValidationStep = {
  from_lifecycle: string;
  to_lifecycle: string;
  effective_validation: string;
  note?: string | null;
};

export type DiagnosticFinding = {
  finding_id: string;
  statement: string;
  epistemic_state: DiagnosticEpistemicState;
  role: DiagnosticFindingRole | null;
  provenance: DiagnosticProvenance;
};

export type DiagnosticHypothesis = {
  hypothesis_id: string;
  statement: string;
  lifecycle: DiagnosticClaimLifecycle;
  effective_validation: DiagnosticEffectiveValidation;
  epistemic_state: DiagnosticEpistemicState;
  provenance: DiagnosticProvenance;
  validation_history: DiagnosticValidationStep[];
};

export type DiagnosticCausalLink = {
  link_id: string;
  source_hypothesis_id: string;
  target_id: string;
  relation: DiagnosticCausalRelation;
};

export type DiagnosticEvidenceLink = {
  link_id: string;
  evidence_id: string;
  relation: DiagnosticEvidenceRelation;
  target_id: string | null;
};

export type DiagnosticConclusion = {
  conclusion_id: string;
  statement: string;
  rationale?: string | null;
  hypothesis_ids: string[];
  finding_ids: string[];
  root_cause_hypothesis_id: string | null;
  lifecycle: DiagnosticClaimLifecycle;
  effective_validation: DiagnosticEffectiveValidation;
  epistemic_state: DiagnosticEpistemicState;
  provenance: DiagnosticProvenance;
  validation_history: DiagnosticValidationStep[];
};

export type Diagnostic = {
  diagnostic_id: string;
  revision_id: string;
  problem_statement: string;
  version: number;
  provenance: DiagnosticProvenance;
  findings: DiagnosticFinding[];
  hypotheses: DiagnosticHypothesis[];
  causal_links: DiagnosticCausalLink[];
  evidence_links: DiagnosticEvidenceLink[];
  conclusions: DiagnosticConclusion[];
};

export type DiagnosticRevisionContext = {
  revision_id: string;
  processo_id: string;
  instancia_id: string | null;
  versao_revisao?: string | null;
  cenario_tipo?: string | null;
  revisao_referencia_id?: string | null;
};

export type DiagnosticEvidenceLinkView = {
  link_id: string;
  evidence_id: string;
  relation: DiagnosticEvidenceRelation;
  target_id: string | null;
  target_kind: string | null;
  resolved_in_revision: boolean;
  evidence: {
    evidence_id: string;
    revisao_id: string;
    tipo: string;
    nome_arquivo?: string | null;
    descricao?: string | null;
  } | null;
};

export type DiagnosticDataQuality = {
  signals: Array<{ code: string; detail?: string | null }>;
  unresolved_evidence_links: string[];
};

export type DiagnosticReadContext = {
  diagnostic: Diagnostic;
  revision: DiagnosticRevisionContext;
  evidence_links: DiagnosticEvidenceLinkView[];
  data_quality: DiagnosticDataQuality;
};

export type DiagnosticSummary = {
  diagnostic_id: string;
  version: number;
  problem_statement: string;
  findings_count: number;
  hypotheses_count: number;
  causal_links_count: number;
  evidence_links_count: number;
  conclusions_count: number;
  has_validated_conclusion: boolean;
  revalidation_attention_required: boolean;
};

export type DiagnosticListResult = {
  revision: DiagnosticRevisionContext;
  items: DiagnosticSummary[];
  total: number;
};

// ---------------------------------------------------------------------------
// Governed proposal contract (opaque — frontend never rebuilds it)
// ---------------------------------------------------------------------------

export type DiagnosticProposal = {
  proposal_handle: string;
  proposal_id: string;
  capability: string;
  resource_type: string;
  resource_id?: string | null;
  exact_change: {
    action: string;
    diagnostic_id: string;
    revision_id?: string;
    expected_version?: number;
    payload?: Record<string, unknown>;
    [key: string]: unknown;
  };
  validation_result?: { ready?: boolean; missing?: string[] } | null;
  consequential_impact?: { persists?: boolean; operation?: string } | null;
  confirmation_requirement?: { explicit_user_confirmation?: boolean } | null;
  expected_postcondition?: Record<string, unknown> | null;
  expires_at?: string | null;
  ready?: boolean;
  act_allowed?: boolean;
};

export type DiagnosticCommitResult = {
  capability?: string;
  data?: { diagnostic?: Partial<Diagnostic> | null };
  [key: string]: unknown;
};

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export async function listRevisionDiagnostics(
  revisaoId: string,
  getAccessToken?: () => string | undefined
): Promise<DiagnosticListResult> {
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}/revisions/${revisaoId}/diagnostics`,
    { headers: buildAuthHeaders(getAccessToken) }
  );
  return parseApiEnvelope<DiagnosticListResult>(response);
}

export async function fetchDiagnostic(
  diagnosticId: string,
  getAccessToken?: () => string | undefined
): Promise<DiagnosticReadContext> {
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}/diagnostics/${diagnosticId}`,
    { headers: buildAuthHeaders(getAccessToken) }
  );
  return parseApiEnvelope<DiagnosticReadContext>(response);
}

export async function prepareCreateDiagnostic(
  revisaoId: string,
  problemStatement: string,
  getAccessToken?: () => string | undefined
): Promise<DiagnosticProposal> {
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}/revisions/${revisaoId}/diagnostics/prepare`,
    {
      method: "POST",
      headers: {
        ...buildAuthHeaders(getAccessToken),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ problem_statement: problemStatement }),
    }
  );
  return parseApiEnvelope<DiagnosticProposal>(response);
}

export async function prepareManageDiagnostic(
  diagnosticId: string,
  action: DiagnosticManageAction,
  payload: Record<string, unknown>,
  getAccessToken?: () => string | undefined
): Promise<DiagnosticProposal> {
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}/diagnostics/${diagnosticId}/prepare`,
    {
      method: "POST",
      headers: {
        ...buildAuthHeaders(getAccessToken),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ action, payload }),
    }
  );
  return parseApiEnvelope<DiagnosticProposal>(response);
}

export async function commitGovernedProposal(
  proposalHandle: string,
  getAccessToken?: () => string | undefined
): Promise<DiagnosticCommitResult> {
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}/governed-proposals/commit`,
    {
      method: "POST",
      headers: {
        ...buildAuthHeaders(getAccessToken),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        proposal_handle: proposalHandle,
        confirmation: true,
      }),
    }
  );
  return parseApiEnvelope<DiagnosticCommitResult>(response);
}
