import type { StrategicIndicatorsChangeRequestListResponse, StrategicIndicatorsSettingsAuditResponse } from "../types/settingsAudit";

const BASE_URL = "/apps/api-delpi/strategic-indicators";

type GetToken = (() => string | undefined) | undefined;

export type FetchAuditParams = {
  limit?: number;
  entityKey?: string;
};

function buildHeaders(getAccessToken?: GetToken): HeadersInit {
  const token = getAccessToken?.();

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}


export async function fetchStrategicIndicatorsSettingsAudit(
  getAccessToken?: GetToken,
  params?: FetchAuditParams,
): Promise<StrategicIndicatorsSettingsAuditResponse> {
  const searchParams = new URLSearchParams();

  if (params?.limit) {
    searchParams.set("limit", String(params.limit));
  }

  if (params?.entityKey) {
    searchParams.set("entity_key", params.entityKey);
  }

  const queryString = searchParams.toString();
  const url = `${BASE_URL}/settings/audit${queryString ? `?${queryString}` : ""}`;

  const response = await fetch(url, {
    method: "GET",
    headers: buildHeaders(getAccessToken),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao carregar auditoria do módulo.");
  }

  return response.json();
}

async function safeReadError(response: Response): Promise<string | null> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    if (typeof data?.message === "string") return data.message;
    return null;
  } catch {
    return null;
  }
}


export async function fetchStrategicIndicatorsChangeRequests(
  getAccessToken?: GetToken,
): Promise<StrategicIndicatorsChangeRequestListResponse> {
  const response = await fetch(BASE_URL, {
    method: "GET",
    headers: buildHeaders(getAccessToken),
  });

  if (!response.ok) {
    throw new Error("Falha ao carregar solicitações administrativas.");
  }

  return response.json();
}

export async function createStrategicIndicatorsChangeRequest(
  payload: {
    title: string;
    description: string;
    target_block: string;
    proposed_payload: Record<string, unknown>;
  },
  getAccessToken?: GetToken,
) {
  const response = await fetch(BASE_URL, {
    method: "POST",
    headers: buildHeaders(getAccessToken),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || "Falha ao criar solicitação.");
  }

  return response.json();
}
