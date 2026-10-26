/** Cliente da BFF — Competências e checklist esperado (P2-READ). */
import { cfApiUrl, httpGet, httpPost } from "./httpClient";

export type CompetenceSheet = "ELETRONICO" | "FISICO";
export type CompetenceItemOrigin = "TOTVS" | "EXTERNAL" | "MIXED";
export type CompetenceItemRecipient = "CONTABIL" | "FISCAL";
export type CompetenceItemBranchScope = "MATRIX" | "BRANCH" | "BOTH";
export type CompetenceItemState =
  | "EXPECTED"
  | "ACCEPTED"
  | "NOT_APPLICABLE"
  | "CANCELLED";

export type ItemValidationScope = "PER_ATTACHMENT" | "WHOLE_SET";

export type RejectionReason =
  | "WRONG_COMPETENCE"
  | "INCOMPLETE"
  | "ILLEGIBLE"
  | "DIVERGENT"
  | "WRONG_DOCUMENT"
  | "OTHER";

export type EvidenceDecisionValue =
  | "ACCEPTED"
  | "REJECTED"
  | "REVERSED";

export type ClosingCompetence = {
  competence_id: string;
  period: string;
  template_version_id: string | null;
  template_version?: number;
  status: "OPEN";
  opened_at: string;
  item_count?: number;
};

export type CompetenceChecklistItem = {
  snapshot_item_id: string;
  item_key: string;
  sort_order: number;
  sheet: CompetenceSheet;
  name: string;
  origin_kind: CompetenceItemOrigin;
  recipient_area: CompetenceItemRecipient | null;
  applicability: string;
  branch_scope: CompetenceItemBranchScope;
  totvs_report_ref: string | null;
  state: CompetenceItemState;
  validation_scope: ItemValidationScope;
  exceptional: boolean;
  revision: number;
  state_reason: string | null;
};

export type CompetenceChecklistItemDetail = CompetenceChecklistItem & {
  purpose: string | null;
  requirement_notes: string | null;
  source_template_item_id: string | null;
  source_version_id: string | null;
};

export type EvidenceDecision = {
  decision_id: string;
  document_id: string | null;
  scope: ItemValidationScope;
  composition: { document_id: string; version_no: number }[];
  decision: EvidenceDecisionValue;
  reason_code: RejectionReason | null;
  comment: string | null;
  result_state: "UNDER_REVIEW" | "ACCEPTED" | null;
  reverses_decision_id: string | null;
  decided_by: string;
  created_at: string;
};

export type ItemDocumentValidation = {
  document_id: string;
  state: string;
  current_version_no: number;
  current_version_decision: {
    decision_id: string;
    decision: EvidenceDecisionValue;
    result_state: "UNDER_REVIEW" | "ACCEPTED" | null;
    reason_code: RejectionReason | null;
    comment: string | null;
    decided_by: string;
    created_at: string;
  } | null;
};

export type ItemValidation = {
  snapshot_item_id: string;
  item_key: string;
  state: CompetenceItemState;
  validation_scope: ItemValidationScope;
  applicability: string;
  documents: ItemDocumentValidation[];
  decisions: EvidenceDecision[];
};

export type ItemCorrection = {
  correction_id: string;
  snapshot_item_id: string;
  item_key: string;
  item_revision: number;
  changes: Record<string, string | null>;
  justification: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
  requested_by: string;
  requested_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_reason: string | null;
};

export type CompetenceItemsQuery = {
  sheet?: CompetenceSheet;
  originKind?: CompetenceItemOrigin;
  recipientArea?: CompetenceItemRecipient;
  branchScope?: CompetenceItemBranchScope;
  state?: CompetenceItemState;
};

type Envelope<T> = { success: boolean; data?: T | null };

function buildQuery(params: Record<string, string | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, value);
  }
  return search.toString();
}

export async function listCompetences(
  options?: { signal?: AbortSignal },
): Promise<ClosingCompetence[]> {
  const envelope = await httpGet<Envelope<{ competences: ClosingCompetence[] }>>(
    cfApiUrl("/closing/competences"),
    options,
  );
  return envelope?.data?.competences ?? [];
}

export async function openCompetence(
  period: string,
  options?: { signal?: AbortSignal },
): Promise<ClosingCompetence> {
  const envelope = await httpPost<Envelope<ClosingCompetence>>(
    cfApiUrl("/closing/competences"),
    { period },
    options,
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia ao abrir a competência.");
  }
  return envelope.data;
}

export async function getCompetence(
  period: string,
  options?: { signal?: AbortSignal },
): Promise<ClosingCompetence> {
  const envelope = await httpGet<Envelope<ClosingCompetence>>(
    cfApiUrl(`/closing/competences/${period}`),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Competência não encontrada.");
  }
  return envelope.data;
}

export async function listCompetenceItems(
  period: string,
  query: CompetenceItemsQuery = {},
  options?: { signal?: AbortSignal },
): Promise<CompetenceChecklistItem[]> {
  const qs = buildQuery({
    sheet: query.sheet,
    origin_kind: query.originKind,
    recipient_area: query.recipientArea,
    branch_scope: query.branchScope,
    state: query.state,
  });
  const envelope = await httpGet<
    Envelope<{ items: CompetenceChecklistItem[] }>
  >(cfApiUrl(`/closing/competences/${period}/items${qs ? `?${qs}` : ""}`), options);
  return envelope?.data?.items ?? [];
}

export async function getCompetenceItem(
  period: string,
  itemKey: string,
  options?: { signal?: AbortSignal },
): Promise<CompetenceChecklistItemDetail> {
  const envelope = await httpGet<Envelope<CompetenceChecklistItemDetail>>(
    cfApiUrl(`/closing/competences/${period}/items/${itemKey}`),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Item do checklist não encontrado.");
  }
  return envelope.data;
}

/* -- P2 validação humana (A2) ------------------------------------------------- */

export type DecisionPayload = {
  decision: "ACCEPTED" | "REJECTED";
  reason_code?: RejectionReason;
  comment?: string;
};

async function postItem<T>(
  path: string,
  body: unknown,
  options?: { signal?: AbortSignal },
): Promise<T> {
  const envelope = await httpPost<Envelope<T>>(cfApiUrl(path), body, options);
  if (!envelope?.data) {
    throw new Error("Resposta vazia da operação.");
  }
  return envelope.data;
}

export function decideDocumentEvidence(
  period: string,
  documentId: string,
  payload: DecisionPayload,
  options?: { signal?: AbortSignal },
) {
  return postItem<EvidenceDecision>(
    `/closing/competences/${period}/documents/${documentId}/validation`,
    payload,
    options,
  );
}

export function decideItemEvidenceSet(
  period: string,
  itemKey: string,
  payload: DecisionPayload,
  options?: { signal?: AbortSignal },
) {
  return postItem<EvidenceDecision>(
    `/closing/competences/${period}/items/${itemKey}/validation`,
    payload,
    options,
  );
}

export function reverseRejection(
  period: string,
  decisionId: string,
  payload: {
    result_state: "UNDER_REVIEW" | "ACCEPTED";
    justification: string;
  },
  options?: { signal?: AbortSignal },
) {
  return postItem<EvidenceDecision>(
    `/closing/competences/${period}/decisions/${decisionId}/reverse`,
    payload,
    options,
  );
}

export function markItemNotApplicable(
  period: string,
  itemKey: string,
  justification: string,
  options?: { signal?: AbortSignal },
) {
  return postItem<CompetenceChecklistItem>(
    `/closing/competences/${period}/items/${itemKey}/not-applicable`,
    { justification },
    options,
  );
}

export function revertItemNotApplicable(
  period: string,
  itemKey: string,
  justification: string,
  options?: { signal?: AbortSignal },
) {
  return postItem<CompetenceChecklistItem>(
    `/closing/competences/${period}/items/${itemKey}/not-applicable/revert`,
    { justification },
    options,
  );
}

export function cancelChecklistItem(
  period: string,
  itemKey: string,
  justification: string,
  options?: { signal?: AbortSignal },
) {
  return postItem<CompetenceChecklistItem>(
    `/closing/competences/${period}/items/${itemKey}/cancel`,
    { justification },
    options,
  );
}

export type ExceptionalItemPayload = {
  sheet: CompetenceSheet;
  name: string;
  justification: string;
  purpose?: string;
  origin_kind?: CompetenceItemOrigin;
  recipient_area?: CompetenceItemRecipient;
  applicability?: "REQUIRED" | "CONDITIONAL" | "OPTIONAL";
  branch_scope?: CompetenceItemBranchScope;
  validation_scope?: ItemValidationScope;
};

export function createExceptionalItem(
  period: string,
  payload: ExceptionalItemPayload,
  options?: { signal?: AbortSignal },
) {
  return postItem<CompetenceChecklistItem>(
    `/closing/competences/${period}/items`,
    payload,
    options,
  );
}

export function requestItemCorrection(
  period: string,
  itemKey: string,
  payload: {
    changes: Record<string, string | null>;
    justification: string;
  },
  options?: { signal?: AbortSignal },
) {
  return postItem<ItemCorrection>(
    `/closing/competences/${period}/items/${itemKey}/corrections`,
    payload,
    options,
  );
}

export function reviewItemCorrection(
  period: string,
  itemKey: string,
  correctionId: string,
  payload: { approve: boolean; review_reason?: string },
  options?: { signal?: AbortSignal },
) {
  return postItem<ItemCorrection>(
    `/closing/competences/${period}/items/${itemKey}/corrections/${correctionId}/review`,
    payload,
    options,
  );
}

export async function listItemCorrections(
  period: string,
  itemKey: string,
  options?: { signal?: AbortSignal },
): Promise<ItemCorrection[]> {
  const envelope = await httpGet<
    Envelope<{ corrections: ItemCorrection[] }>
  >(
    cfApiUrl(
      `/closing/competences/${period}/items/${itemKey}/corrections`,
    ),
    options,
  );
  return envelope?.data?.corrections ?? [];
}

export async function getItemValidation(
  period: string,
  itemKey: string,
  options?: { signal?: AbortSignal },
): Promise<ItemValidation> {
  const envelope = await httpGet<Envelope<ItemValidation>>(
    cfApiUrl(
      `/closing/competences/${period}/items/${itemKey}/validation`,
    ),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Validação do item não encontrada.");
  }
  return envelope.data;
}
