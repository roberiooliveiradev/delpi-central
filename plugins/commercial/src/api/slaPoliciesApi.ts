import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import { commercialApiUrl, httpGet } from "./httpClient";

export type SlaPolicyRow = {
  id: string;
  code: string;
  name: string;
  appliesTo: string;
  durationHours: number;
};

export async function getSlaPolicies(signal?: AbortSignal): Promise<{
  items: SlaPolicyRow[];
  configured: boolean;
}> {
  const response = await httpGet<ApiSuccessResponse<{ items: SlaPolicyRow[]; configured: boolean }>>(
    commercialApiUrl("/settings/sla-policies"),
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar SLA.");
}
