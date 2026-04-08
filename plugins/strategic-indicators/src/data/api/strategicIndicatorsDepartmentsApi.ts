import type { StrategicIndicatorsDepartmentsResponse } from "../types/departments";

const BASE_URL = "/apps/api-delpi/strategic-indicators";

type GetToken = (() => string | undefined) | undefined;

export type FetchStrategicIndicatorsDepartmentsParams = {
  competence?: string;
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
  competence?: string;
  startDate?: string;
  endDate?: string;
}) {
  const query = new URLSearchParams();

  if (params.competence) query.set("competence", params.competence);
  if (params.startDate) query.set("start_date", params.startDate);
  if (params.endDate) query.set("end_date", params.endDate);

  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

export async function fetchStrategicIndicatorsDepartments({
  competence,
  startDate,
  endDate,
  getAccessToken,
  signal,
}: FetchStrategicIndicatorsDepartmentsParams): Promise<StrategicIndicatorsDepartmentsResponse> {
  const response = await fetch(
    `${BASE_URL}/departments${buildQuery({
      competence,
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
    throw new Error(message || "Falha ao carregar departamentos do módulo.");
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