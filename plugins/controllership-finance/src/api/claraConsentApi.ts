/** Cliente da BFF — superfície de consentimento step-up da CLARA. */
import { cfApiUrl, httpGet, httpPostStepUp } from "./httpClient";

export type ClaraChallengeView = {
  challenge_id: string;
  status: string;
  created_at: string;
  approved_at: string | null;
  expires_at: string;
};

export type ClaraOperationPresentation = {
  displayable: boolean;
  action: string;
  target: string;
  effect: string | null;
  motivation: string | null;
  summary: string;
};

export type ClaraBatchOperation = {
  index: number;
  seq: number;
  capability: string;
  viability: "executable" | "blocked";
  state: string;
  presentation: ClaraOperationPresentation;
  resource_type: string | null;
  resource_key: string | null;
  period: string | null;
  depends_on: number[];
  block_reason: string | null;
  block_message: string | null;
  missing_params: string[];
};

export type ClaraBatchConsentView = {
  batch_id: string;
  status: string;
  plan_hash: string;
  consent_mode: string;
  actor_sub: string;
  expires_at: string;
  created_at: string;
  confirmed_at: string | null;
  challenge: ClaraChallengeView | null;
  competence: { period: string | null; period_label: string | null };
  totals: {
    total: number;
    executable: number;
    blocked: number;
    dependent: number;
  };
  consentable: boolean;
  consent_block_reason: string | null;
  operations: ClaraBatchOperation[];
};

export type ClaraProposalConsentView = {
  proposal_id: string;
  capability: string;
  resource_type: string;
  resource_key: string;
  params: Record<string, unknown>;
  presentation: ClaraOperationPresentation;
  expected_state: Record<string, unknown>;
  execution_state: string;
  consented_at: string | null;
  expires_at: string;
  created_at: string;
  challenge: ClaraChallengeView | null;
  period: string | null;
  period_label: string | null;
  consentable: boolean;
  consent_block_reason: string | null;
};

export type ClaraBatchConsentResult = {
  batch_id: string;
  status: string;
  consent_mode: string;
  challenge_id: string;
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
  challengeId: string,
): Promise<ClaraBatchConsentResult> {
  const envelope = await httpPostStepUp<
    Envelope<ClaraBatchConsentResult>
  >(cfApiUrl(`/clara/batches/${batchId}/consent`), {
    challenge_id: challengeId,
  });
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
  challengeId: string,
): Promise<ClaraProposalConsentResult> {
  const envelope = await httpPostStepUp<
    Envelope<ClaraProposalConsentResult>
  >(cfApiUrl(`/clara/proposals/${proposalId}/consent`), {
    challenge_id: challengeId,
  });
  if (!envelope?.data) throw new Error("Resposta vazia do servidor.");
  return envelope.data;
}
