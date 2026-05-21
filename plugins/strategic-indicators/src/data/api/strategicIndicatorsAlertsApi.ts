import type { StrategicIndicatorsAlertsResponse } from "../types/alerts";
import { buildStrategicIndicatorsApiError } from "./strategicIndicatorsApiErrors";

import { STRATEGIC_INDICATORS_API_BASE } from "./strategicIndicatorsApiBase";

const BASE_URL = STRATEGIC_INDICATORS_API_BASE;

type GetToken = (() => string | undefined) | undefined;

export type FetchStrategicIndicatorsAlertsParams = {
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

  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

export async function fetchStrategicIndicatorsAlerts({
  departmentId,
  branch,
  competence,
  startDate,
  endDate,
  getAccessToken,
  signal,
}: FetchStrategicIndicatorsAlertsParams): Promise<StrategicIndicatorsAlertsResponse> {
  const response = await fetch(
    `${BASE_URL}/alerts${buildQuery({
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
      surface: "Lista de alertas",
      route: "/alerts",
      method: "GET",
      competence: competence ?? null,
      branch: branch ?? null,
      departmentId: departmentId ?? null,
    });
  }

  return response.json();
}