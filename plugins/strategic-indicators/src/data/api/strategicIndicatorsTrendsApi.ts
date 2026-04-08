import type { StrategicIndicatorsTrendsResponse } from "../types/trends";

const BASE_URL = "/apps/api-delpi/strategic-indicators";

type GetToken = (() => string | undefined) | undefined;

export type FetchStrategicIndicatorsTrendsParams = {
  competence?: string;
  months?: number;
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
  months?: number;
}) {
  const query = new URLSearchParams();

  if (params.competence) query.set("competence", params.competence);
  if (typeof params.months === "number") query.set("months", String(params.months));

  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

export async function fetchStrategicIndicatorsTrends({
  competence,
  months,
  getAccessToken,
  signal,
}: FetchStrategicIndicatorsTrendsParams): Promise<StrategicIndicatorsTrendsResponse> {
  const response = await fetch(
    `${BASE_URL}/trends${buildQuery({
      competence,
      months,
    })}`,
    {
      method: "GET",
      headers: buildHeaders(getAccessToken),
      signal,
    },
  );

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao carregar tendências do módulo.");
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