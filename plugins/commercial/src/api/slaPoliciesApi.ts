import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import {
  commercialApiUrl,
  httpDelete,
  httpGet,
  httpPatch,
  httpPost,
} from "./httpClient";

export const SLA_APPLIES_TO_VALUES = [
  "task",
  "sample",
  "order_confirmation",
  "offer_stage",
] as const;

export type SlaAppliesTo = (typeof SLA_APPLIES_TO_VALUES)[number];

export type SlaPolicyRow = {
  id: string;
  code: string;
  name: string;
  appliesTo: SlaAppliesTo | string;
  durationHours: number;
  calendarCode?: string | null;
  active: boolean;
};

export type SlaPolicyListResult = {
  items: SlaPolicyRow[];
  configured: boolean;
  includeInactive?: boolean;
};

export type SlaPolicyWriteInput = {
  code: string;
  name: string;
  appliesTo: SlaAppliesTo;
  durationHours: number;
  calendarCode?: string | null;
  active?: boolean;
};

export type SlaPolicyUpdateInput = Partial<SlaPolicyWriteInput>;

/** @deprecated Prefer listSlaPolicies({ includeInactive: true }) na Administração. */
export async function getSlaPolicies(signal?: AbortSignal): Promise<SlaPolicyListResult> {
  return listSlaPolicies({ includeInactive: false, signal });
}

export async function listSlaPolicies(options?: {
  includeInactive?: boolean;
  signal?: AbortSignal;
}): Promise<SlaPolicyListResult> {
  const params = new URLSearchParams();
  if (options?.includeInactive) params.set("include_inactive", "true");
  const query = params.toString();
  const response = await httpGet<ApiSuccessResponse<SlaPolicyListResult>>(
    commercialApiUrl(`/settings/sla-policies${query ? `?${query}` : ""}`),
    { signal: options?.signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar políticas de SLA.");
}

export async function createSlaPolicy(
  body: SlaPolicyWriteInput,
): Promise<SlaPolicyRow> {
  const response = await httpPost<ApiSuccessResponse<SlaPolicyRow>>(
    commercialApiUrl("/settings/sla-policies"),
    {
      code: body.code,
      name: body.name,
      appliesTo: body.appliesTo,
      durationHours: body.durationHours,
      calendarCode: body.calendarCode ?? null,
      active: body.active ?? true,
    },
  );
  return unwrapEnvelope(response, "Erro ao criar política de SLA.");
}

export async function updateSlaPolicy(
  policyId: string,
  body: SlaPolicyUpdateInput,
): Promise<SlaPolicyRow> {
  const response = await httpPatch<ApiSuccessResponse<SlaPolicyRow>>(
    commercialApiUrl(`/settings/sla-policies/${encodeURIComponent(policyId)}`),
    body as Record<string, unknown>,
  );
  return unwrapEnvelope(response, "Erro ao atualizar política de SLA.");
}

export async function deactivateSlaPolicy(policyId: string): Promise<SlaPolicyRow> {
  const response = await httpDelete<ApiSuccessResponse<SlaPolicyRow>>(
    commercialApiUrl(`/settings/sla-policies/${encodeURIComponent(policyId)}`),
  );
  return unwrapEnvelope(response, "Erro ao desativar política de SLA.");
}
