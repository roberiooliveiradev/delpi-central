/** Cliente da BFF — superfície de consentimento step-up da CLARA. */
import { cfApiUrl, httpGet, httpPostStepUp } from "./httpClient";

export type ClaraBatchOperation = {
  seq: number;
  capability: string;
  resource_type: string;
  resource_key: string;
  state: string;
  depends_on: unknown[];
};

export type ClaraBatchConsentView = {
  batch_id: string;
  status: string;
  plan_hash: string;
  consent_mode: string;
  expires_at: string;
  created_at: string;
  operations: ClaraBatchOperation[];
};

export type ClaraProposalConsentView = {
  proposal_id: string;
  capability: string;
  resource_type: string;
  resource_key: string;
  params: Record<string, unknown>;
  expected_state: Record<string, unknown>;
  execution_state: string;
  consented_at: string | null;
  expires_at: string;
  created_at: string;
};

export type ClaraBatchConsentResult = {
  batch_id: string;
  status: string;
  consent_mode: string;
  confirmed_at: string;
};

export type ClaraProposalConsentResult = {
  proposal_id: string;
  consented_at: string;
};

type Envelope<T> = { data?: T };

export async function getClaraBatchConsentView(
  batchId: string,
  signal?: AbortSignal,
): Promise<ClaraBatchConsentView | null> {
  const envelope = await httpGet<Envelope<ClaraBatchConsentView>>(
    cfApiUrl(`/clara/batches/${batchId}`),
    { signal },
  );
  return envelope?.data ?? null;
}

export async function recordClaraBatchConsent(
  batchId: string,
): Promise<ClaraBatchConsentResult> {
  const envelope = await httpPostStepUp<
    Envelope<ClaraBatchConsentResult>
  >(cfApiUrl(`/clara/batches/${batchId}/consent`), {});
  if (!envelope?.data) throw new Error("Resposta vazia do servidor.");
  return envelope.data;
}

export async function getClaraProposalConsentView(
  proposalId: string,
  signal?: AbortSignal,
): Promise<ClaraProposalConsentView | null> {
  const envelope = await httpGet<Envelope<ClaraProposalConsentView>>(
    cfApiUrl(`/clara/proposals/${proposalId}`),
    { signal },
  );
  return envelope?.data ?? null;
}

export async function recordClaraProposalConsent(
  proposalId: string,
): Promise<ClaraProposalConsentResult> {
  const envelope = await httpPostStepUp<
    Envelope<ClaraProposalConsentResult>
  >(cfApiUrl(`/clara/proposals/${proposalId}/consent`), {});
  if (!envelope?.data) throw new Error("Resposta vazia do servidor.");
  return envelope.data;
}
