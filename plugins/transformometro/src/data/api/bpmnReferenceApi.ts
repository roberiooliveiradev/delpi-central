import {
  TRANSFORMOMETRO_API_BASE,
  buildAuthHeaders,
} from "./transformometroApiBase";
import { parseApiEnvelope } from "./transformometroHttp";

export type BpmnReferenceResolutionState =
  | "resolved"
  | "unavailable"
  | "inaccessible_or_missing";

export type ProcessBpmnReference = {
  reference_id: string;
  processo_id: string;
  model_id: string;
  revision_number: number;
  created_by?: string;
  updated_by?: string;
  created_at?: string;
  updated_at?: string;
};

/** DERIVED / REMOTE READ — nunca é autoridade persistida. */
export type BpmnReferenceResolved = {
  state: BpmnReferenceResolutionState;
  model_display_name?: string;
  model_archived?: boolean;
  latest_revision_number?: number | null;
  revision_id?: string;
  revision_name?: string;
  revision_description?: string;
  revision_created_at?: string;
  revision_created_by_name?: string;
  artifact_sha256?: string;
};

export type ProcessBpmnReferencePayload = {
  reference: ProcessBpmnReference | null;
  resolved: BpmnReferenceResolved | null;
};

export type BpmnModelCandidate = {
  model_id: string;
  display_name?: string;
  latest_revision_number?: number | null;
  archived?: boolean;
};

export type BpmnRevisionCandidate = {
  revision_number: number;
  revision_id?: string;
  name?: string;
  description?: string;
  origin?: string;
  created_at?: string;
  created_by_name?: string;
};

type GetToken = (() => string | undefined) | undefined;

async function request<T>(
  path: string,
  getAccessToken: GetToken,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...buildAuthHeaders(getAccessToken),
      ...(init?.headers ?? {}),
    },
  });
  return parseApiEnvelope<T>(response);
}

export function fetchProcessBpmnReference(
  processoId: string,
  getAccessToken: GetToken
): Promise<ProcessBpmnReferencePayload> {
  return request(`/processos/${processoId}/bpmn-reference`, getAccessToken);
}

export function setProcessBpmnReference(
  processoId: string,
  body: { model_id: string; revision_number: number },
  getAccessToken: GetToken
): Promise<ProcessBpmnReferencePayload> {
  return request(`/processos/${processoId}/bpmn-reference`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function removeProcessBpmnReference(
  processoId: string,
  getAccessToken: GetToken
): Promise<ProcessBpmnReferencePayload> {
  return request(`/processos/${processoId}/bpmn-reference`, getAccessToken, {
    method: "DELETE",
  });
}

export function fetchBpmnModelCandidates(
  processoId: string,
  getAccessToken: GetToken
): Promise<{ state: string; items: BpmnModelCandidate[] }> {
  return request(
    `/processos/${processoId}/bpmn-reference/candidates`,
    getAccessToken
  );
}

export function fetchBpmnModelRevisions(
  processoId: string,
  modelId: string,
  getAccessToken: GetToken
): Promise<{ state: string; model_id: string; items: BpmnRevisionCandidate[] }> {
  return request(
    `/processos/${processoId}/bpmn-reference/candidates/${modelId}/revisions`,
    getAccessToken
  );
}

/** Deep links product-owned do BPMN Modeler (App.tsx). */
export function bpmnModelUrl(modelId: string): string {
  return `/apps/bpmn-modeler/models/${modelId}`;
}

export function bpmnRevisionUrl(modelId: string, revisionNumber: number): string {
  return `/apps/bpmn-modeler/models/${modelId}/revisions/${revisionNumber}`;
}
