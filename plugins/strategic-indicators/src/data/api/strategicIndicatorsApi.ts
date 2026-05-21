import type { StrategicIndicatorsResponse } from "../types/indicators";
import { buildStrategicIndicatorsApiError } from "./strategicIndicatorsApiErrors";

import { STRATEGIC_INDICATORS_API_BASE } from "./strategicIndicatorsApiBase";

const BASE_URL = STRATEGIC_INDICATORS_API_BASE;

type GetToken = (() => string | undefined) | undefined;

export type FetchStrategicIndicatorsParams = {
  departmentId?: string;
  branch?: string;
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
  departmentId?: string;
  branch?: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
}) {
  const query = new URLSearchParams();

  if (params.departmentId) query.set("department_id", params.departmentId);
  if (params.branch) query.set("branch", params.branch);
  if (params.competence) query.set("competence", params.competence);
  if (params.startDate) query.set("start_date", params.startDate);
  if (params.endDate) query.set("end_date", params.endDate);

  const asString = query.toString();
  return asString ? `?${asString}` : "";
}

export async function fetchStrategicIndicators({
  departmentId,
  branch,
  competence,
  startDate,
  endDate,
  getAccessToken,
  signal,
}: FetchStrategicIndicatorsParams): Promise<StrategicIndicatorsResponse> {
  const response = await fetch(
    `${BASE_URL}/indicators${buildQuery({
      departmentId,
      branch,
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
    throw await buildStrategicIndicatorsApiError(response, {
      surface: "Lista de indicadores",
      route: "/indicators",
      method: "GET",
      competence: competence ?? null,
      branch: branch ?? null,
      departmentId: departmentId ?? null,
    });
  }

  return response.json();
}