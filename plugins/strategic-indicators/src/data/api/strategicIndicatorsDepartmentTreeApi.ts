import type { StrategicIndicatorsDepartmentTreeResponse } from "../types/departmentTreeBundle";
import { buildStrategicIndicatorsApiError } from "./strategicIndicatorsApiErrors";
import { STRATEGIC_INDICATORS_API_BASE } from "./strategicIndicatorsApiBase";

const BASE_URL = STRATEGIC_INDICATORS_API_BASE;

type GetToken = (() => string | undefined) | undefined;

export type FetchStrategicIndicatorsDepartmentTreeParams = {
  viewMode?: "consolidated" | "branch";
  branch?: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
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
  viewMode?: string;
  branch?: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
  months?: number;
}) {
  const query = new URLSearchParams();

  if (params.viewMode) query.set("view_mode", params.viewMode);
  if (params.branch) query.set("branch", params.branch);
  if (params.competence) query.set("competence", params.competence);
  if (params.startDate) query.set("start_date", params.startDate);
  if (params.endDate) query.set("end_date", params.endDate);
  if (typeof params.months === "number") query.set("months", String(params.months));

  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

export async function fetchStrategicIndicatorsDepartmentTree({
  viewMode = "consolidated",
  branch,
  competence,
  startDate,
  endDate,
  months = 6,
  getAccessToken,
  signal,
}: FetchStrategicIndicatorsDepartmentTreeParams): Promise<StrategicIndicatorsDepartmentTreeResponse> {
  const response = await fetch(
    `${BASE_URL}/departments/tree${buildQuery({
      viewMode,
      branch,
      competence,
      startDate,
      endDate,
      months,
    })}`,
    {
      method: "GET",
      headers: buildHeaders(getAccessToken),
      signal,
    },
  );

  if (!response.ok) {
    throw await buildStrategicIndicatorsApiError(response, {
      surface: "Árvore de departamentos",
      route: "/departments/tree",
      method: "GET",
    });
  }

  return response.json() as Promise<StrategicIndicatorsDepartmentTreeResponse>;
}
