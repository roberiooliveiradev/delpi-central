import type {
  StrategicIndicatorsDepartmentTreeResponse,
  StrategicIndicatorsTreeSnapshotResponse,
  StrategicIndicatorsTreeTrendsResponse,
  StrategicIndicatorsTreeLoadJobCreateResponse,
  StrategicIndicatorsTreeLoadJobStatusResponse,
} from "../types/departmentTreeBundle";
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
  months = 3,
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

export type FetchTreeSnapshotParams = Omit<
  FetchStrategicIndicatorsDepartmentTreeParams,
  "months"
>;

export async function fetchDepartmentTreeSnapshot({
  viewMode = "consolidated",
  branch,
  competence,
  startDate,
  endDate,
  getAccessToken,
  signal,
}: FetchTreeSnapshotParams): Promise<StrategicIndicatorsTreeSnapshotResponse> {
  const response = await fetch(
    `${BASE_URL}/departments/tree/snapshot${buildQuery({
      viewMode,
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
      surface: "Snapshot da árvore",
      route: "/departments/tree/snapshot",
      method: "GET",
    });
  }

  return response.json() as Promise<StrategicIndicatorsTreeSnapshotResponse>;
}

export type FetchTreeTrendsParams = FetchStrategicIndicatorsDepartmentTreeParams;

export async function fetchDepartmentTreeTrends({
  viewMode = "consolidated",
  branch,
  competence,
  startDate,
  endDate,
  months = 3,
  getAccessToken,
  signal,
}: FetchTreeTrendsParams): Promise<StrategicIndicatorsTreeTrendsResponse> {
  const response = await fetch(
    `${BASE_URL}/departments/tree/trends${buildQuery({
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
      surface: "Trends da árvore",
      route: "/departments/tree/trends",
      method: "GET",
    });
  }

  return response.json() as Promise<StrategicIndicatorsTreeTrendsResponse>;
}

export type CreateTreeLoadJobParams = FetchStrategicIndicatorsDepartmentTreeParams;

export async function createDepartmentTreeLoadJob({
  viewMode = "consolidated",
  branch,
  competence,
  startDate,
  endDate,
  months = 3,
  getAccessToken,
  signal,
}: CreateTreeLoadJobParams): Promise<StrategicIndicatorsTreeLoadJobCreateResponse> {
  const response = await fetch(`${BASE_URL}/departments/tree/load-job`, {
    method: "POST",
    headers: buildHeaders(getAccessToken),
    signal,
    body: JSON.stringify({
      view_mode: viewMode,
      branch,
      competence,
      start_date: startDate,
      end_date: endDate,
      months,
    }),
  });

  if (!response.ok) {
    throw await buildStrategicIndicatorsApiError(response, {
      surface: "Snapshot da árvore",
      route: "/departments/tree/load-job",
      method: "POST",
    });
  }

  return response.json() as Promise<StrategicIndicatorsTreeLoadJobCreateResponse>;
}

export async function fetchStrategicIndicatorsJobStatus({
  jobId,
  getAccessToken,
  signal,
}: {
  jobId: string;
  getAccessToken?: GetToken;
  signal?: AbortSignal;
}): Promise<StrategicIndicatorsTreeLoadJobStatusResponse> {
  const response = await fetch(`${BASE_URL}/jobs/${jobId}`, {
    method: "GET",
    headers: buildHeaders(getAccessToken),
    signal,
  });

  if (!response.ok) {
    throw await buildStrategicIndicatorsApiError(response, {
      surface: "Snapshot da árvore",
      route: "/jobs/{job_id}",
      method: "GET",
    });
  }

  return response.json() as Promise<StrategicIndicatorsTreeLoadJobStatusResponse>;
}
