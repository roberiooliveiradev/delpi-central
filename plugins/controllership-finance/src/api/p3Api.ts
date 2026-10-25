/** Cliente da BFF — P3 cutoff, conciliação e revalidação (doc 10). */
import { cfApiUrl, httpGet, httpPost, httpPut } from "./httpClient";

export type P3State =
  | "WAITING_FOR_CUTOFF"
  | "REVALIDATION_REQUIRED"
  | "READY_TO_CLOSE"
  | "STOCK_CLOSED";

export type ReconciliationDomain = "ENTRADAS_SAIDAS" | "P7" | "H02";

export type SourceState =
  | "AVAILABLE"
  | "STALE"
  | "UNAVAILABLE"
  | "PARTIAL"
  | "ERROR";

export type Reconciliation = {
  domain: ReconciliationDomain;
  source_state: SourceState;
  expected_amount: string | null;
  reported_amount: string | null;
  divergence: string | null;
  fetched_at: string | null;
  rule_version: string | null;
  provenance: Record<string, unknown> | null;
  revision?: number;
  updated_at?: string;
};

export type P3Cutoff = {
  cutoff_id: string;
  competence_id: string;
  confirmed_by: string;
  confirmed_at: string;
  notes: string | null;
  revision: number;
};

export type P3Revalidation = {
  revalidation_id: string;
  validated_by: string;
  validated_at: string;
  result: "VALID" | "STALE_INPUT";
  input_fingerprint: string;
  notes: string | null;
};

export type P3Status = {
  period: string;
  state: P3State;
  canonical_stock_state: "OPEN" | "CLOSED" | "UNAVAILABLE";
  cutoff: P3Cutoff | null;
  reconciliations: Reconciliation[];
  last_revalidation: P3Revalidation | null;
  revalidation_valid: boolean;
  input_fingerprint: string;
  blockers: string[];
};

export type P3AuditEvent = {
  event_id: number;
  event_type: string;
  actor_subject: string;
  detail: Record<string, unknown>;
  created_at: string;
};

type Envelope<T> = { data?: T };

function base(period: string): string {
  return `/closing/competences/${period}/p3`;
}

export async function getP3State(
  period: string,
  signal?: AbortSignal,
): Promise<P3Status | null> {
  const envelope = await httpGet<Envelope<P3Status>>(
    cfApiUrl(base(period)),
    { signal },
  );
  return envelope?.data ?? null;
}

export async function listP3Events(
  period: string,
  signal?: AbortSignal,
): Promise<P3AuditEvent[]> {
  const envelope = await httpGet<Envelope<{ items: P3AuditEvent[] }>>(
    cfApiUrl(`${base(period)}/events`),
    { signal },
  );
  return envelope?.data?.items ?? [];
}

export async function confirmP3Cutoff(
  period: string,
  notes?: string,
): Promise<P3Cutoff | null> {
  const envelope = await httpPost<Envelope<{ cutoff: P3Cutoff }>>(
    cfApiUrl(`${base(period)}/cutoff`),
    { notes },
  );
  return envelope?.data?.cutoff ?? null;
}

export async function upsertP3Reconciliation(
  period: string,
  domain: ReconciliationDomain,
  input: {
    sourceState: SourceState;
    expectedAmount?: string;
    reportedAmount?: string;
    ruleVersion?: string;
    provenance?: Record<string, unknown>;
    revision?: number;
  },
): Promise<Reconciliation | null> {
  const envelope = await httpPut<
    Envelope<{ reconciliation: Reconciliation }>
  >(cfApiUrl(`${base(period)}/reconciliations/${domain}`), {
    source_state: input.sourceState,
    expected_amount: input.expectedAmount,
    reported_amount: input.reportedAmount,
    rule_version: input.ruleVersion,
    provenance: input.provenance,
    revision: input.revision,
  });
  return envelope?.data?.reconciliation ?? null;
}

export async function revalidateP3(
  period: string,
  notes?: string,
): Promise<P3Revalidation | null> {
  const envelope = await httpPost<
    Envelope<{ revalidation: P3Revalidation }>
  >(cfApiUrl(`${base(period)}/revalidations`), { notes });
  return envelope?.data?.revalidation ?? null;
}
