import type { StrategicIndicatorsResponse } from "../types/indicators";

const BASE_URL = "/apps/api-delpi/strategic-indicators";

type GetToken = (() => string | undefined) | undefined;

export type FetchStrategicIndicatorsParams = {
  departmentId?: string;
  startDate?: string;
  endDate?: string;
  getAccessToken?: GetToken;
  signal?: AbortSignal;
};

function buildHeaders(getAccessToken?: GetToken): HeadersInit {
  const token = getAccessToken?.();

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function buildQuery(params: {
  departmentId?: string;
  startDate?: string;
  endDate?: string;
}) {
  const query = new URLSearchParams();

  if (params.departmentId) query.set("department_id", params.departmentId);
  if (params.startDate) query.set("start_date", params.startDate);
  if (params.endDate) query.set("end_date", params.endDate);

  const asString = query.toString();
  return asString ? `?${asString}` : "";
}

export async function fetchStrategicIndicators({
  departmentId,
  startDate,
  endDate,
  getAccessToken,
  signal,
}: FetchStrategicIndicatorsParams): Promise<StrategicIndicatorsResponse> {
  const response = await fetch(
    `${BASE_URL}/indicators${buildQuery({
      departmentId,
      startDate,
      endDate,
    })}`,
    {
      method: "GET",
      headers: buildHeaders(getAccessToken),
      signal,
    },
  );

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao carregar indicadores do módulo.");
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