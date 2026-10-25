/** Cliente da BFF — P4 pendências e classificações (doc 11). */
import { cfApiUrl, httpGet, httpPost } from "./httpClient";

export type PendencyState =
  | "OPEN"
  | "IN_ANALYSIS"
  | "WAITING_EXTERNAL"
  | "RESOLVED"
  | "DISMISSED";

export type PendencyKind =
  | "MISSING_EVIDENCE"
  | "VALIDATION_REJECTED"
  | "RECONCILIATION_DIVERGENCE"
  | "STRUCTURAL_CORRECTION"
  | "EXTERNAL_DEPENDENCY"
  | "OTHER";

export type Pendency = {
  pendency_id: string;
  competence_id: string;
  snapshot_item_id: string | null;
  kind: PendencyKind;
  title: string;
  description: string | null;
  state: PendencyState;
  queue: string | null;
  responsible_subject: string | null;
  branch_scope: "MATRIX" | "BRANCH" | "BOTH";
  suggested_classification: string | null;
  suggestion_rationale: string | null;
  suggestion_source: "DETERMINISTIC" | "AI" | "MANUAL" | null;
  confirmed_classification: string | null;
  classification_reason: string | null;
  resolution_notes: string | null;
  dismiss_justification: string | null;
  revision: number;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type PendencyHistoryEvent = {
  event_id: number;
  event_type: string;
  actor_subject: string;
  detail: Record<string, unknown>;
  created_at: string;
};

export type PendencyList = {
  items: Pendency[];
  limit: number;
  offset: number;
};

export type PendencyFilters = {
  state?: PendencyState;
  kind?: PendencyKind;
  responsible?: string;
  branchScope?: string;
  limit?: number;
  offset?: number;
};

type Envelope<T> = { data?: T };

function base(period: string): string {
  return `/closing/competences/${period}/pendencies`;
}

export async function listPendencies(
  period: string,
  filters: PendencyFilters = {},
  signal?: AbortSignal,
): Promise<PendencyList> {
  const params = new URLSearchParams();
  if (filters.state) params.set("state", filters.state);
  if (filters.kind) params.set("kind", filters.kind);
  if (filters.responsible) params.set("responsible", filters.responsible);
  if (filters.branchScope) params.set("branch_scope", filters.branchScope);
  params.set("limit", String(filters.limit ?? 50));
  params.set("offset", String(filters.offset ?? 0));
  const envelope = await httpGet<Envelope<PendencyList>>(
    cfApiUrl(`${base(period)}?${params.toString()}`),
    { signal },
  );
  return envelope?.data ?? { items: [], limit: 50, offset: 0 };
}

export async function getPendency(
  period: string,
  pendencyId: string,
  signal?: AbortSignal,
): Promise<Pendency | null> {
  const envelope = await httpGet<Envelope<{ pendency: Pendency }>>(
    cfApiUrl(`${base(period)}/${pendencyId}`),
    { signal },
  );
  return envelope?.data?.pendency ?? null;
}

export async function listPendencyHistory(
  period: string,
  pendencyId: string,
  signal?: AbortSignal,
): Promise<{ pendency: Pendency; events: PendencyHistoryEvent[] } | null> {
  const envelope = await httpGet<
    Envelope<{ pendency: Pendency; events: PendencyHistoryEvent[] }>
  >(cfApiUrl(`${base(period)}/${pendencyId}/history`), { signal });
  return envelope?.data ?? null;
}

export async function createPendency(
  period: string,
  input: {
    kind: PendencyKind;
    title: string;
    description?: string;
    snapshotItemId?: string;
    queue?: string;
    responsibleSubject?: string;
    branchScope?: string;
    suggestedClassification?: string;
    suggestionRationale?: string;
    suggestionSource?: "DETERMINISTIC" | "AI" | "MANUAL";
  },
): Promise<Pendency | null> {
  const envelope = await httpPost<Envelope<{ pendency: Pendency }>>(
    cfApiUrl(base(period)),
    {
      kind: input.kind,
      title: input.title,
      description: input.description,
      snapshot_item_id: input.snapshotItemId,
      queue: input.queue,
      responsible_subject: input.responsibleSubject,
      branch_scope: input.branchScope,
      suggested_classification: input.suggestedClassification,
      suggestion_rationale: input.suggestionRationale,
      suggestion_source: input.suggestionSource,
    },
  );
  return envelope?.data?.pendency ?? null;
}

export async function claimPendency(
  period: string,
  pendencyId: string,
  revision: number,
): Promise<Pendency | null> {
  const envelope = await httpPost<Envelope<{ pendency: Pendency }>>(
    cfApiUrl(`${base(period)}/${pendencyId}/claim`),
    { revision },
  );
  return envelope?.data?.pendency ?? null;
}

export async function reassignPendency(
  period: string,
  pendencyId: string,
  newResponsible: string,
  revision: number,
): Promise<Pendency | null> {
  const envelope = await httpPost<Envelope<{ pendency: Pendency }>>(
    cfApiUrl(`${base(period)}/${pendencyId}/reassign`),
    { new_responsible: newResponsible, revision },
  );
  return envelope?.data?.pendency ?? null;
}

export async function transitionPendency(
  period: string,
  pendencyId: string,
  input: {
    toState: PendencyState;
    revision: number;
    justification?: string;
    notes?: string;
  },
): Promise<Pendency | null> {
  const envelope = await httpPost<Envelope<{ pendency: Pendency }>>(
    cfApiUrl(`${base(period)}/${pendencyId}/transition`),
    {
      to_state: input.toState,
      revision: input.revision,
      justification: input.justification,
      notes: input.notes,
    },
  );
  return envelope?.data?.pendency ?? null;
}

export async function confirmPendencyClassification(
  period: string,
  pendencyId: string,
  input: {
    classification: string;
    reason?: string;
    revision: number;
  },
): Promise<Pendency | null> {
  const envelope = await httpPost<Envelope<{ pendency: Pendency }>>(
    cfApiUrl(`${base(period)}/${pendencyId}/classification`),
    {
      classification: input.classification,
      reason: input.reason,
      revision: input.revision,
    },
  );
  return envelope?.data?.pendency ?? null;
}
