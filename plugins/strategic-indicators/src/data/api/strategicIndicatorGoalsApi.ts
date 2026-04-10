import type {
  CreateStrategicIndicatorGoalRequest,
  StrategicIndicatorGoalHistoryResponse,
  StrategicIndicatorGoalListResponse,
  UpdateStrategicIndicatorGoalRequest,
} from "../types/indicatorGoals";

const BASE_URL = "/apps/api-delpi/strategic-indicators";

type GetToken = (() => string | undefined) | undefined;

export type FetchIndicatorGoalsParams = {
  indicatorId?: string;
  goalYear?: number;
  departmentId?: string;
  activeOnly?: boolean;
};

function buildHeaders(getAccessToken?: GetToken): HeadersInit {
  const token = getAccessToken?.();

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function fetchStrategicIndicatorGoals(
  getAccessToken?: GetToken,
  params?: FetchIndicatorGoalsParams,
  signal?: AbortSignal,
): Promise<StrategicIndicatorGoalListResponse> {
  const searchParams = new URLSearchParams();

  if (params?.indicatorId) {
    searchParams.set("indicator_id", params.indicatorId);
  }

  if (typeof params?.goalYear === "number") {
    searchParams.set("goal_year", String(params.goalYear));
  }

  if (params?.departmentId) {
    searchParams.set("department_id", params.departmentId);
  }

  if (params?.activeOnly) {
    searchParams.set("active_only", "true");
  }

  const queryString = searchParams.toString();
  const url = `${BASE_URL}/indicator-goals${queryString ? `?${queryString}` : ""}`;

  const response = await fetch(url, {
    method: "GET",
    headers: buildHeaders(getAccessToken),
    signal,
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Failed to load indicator goals.");
  }

  return response.json();
}

export async function fetchStrategicIndicatorGoalHistory(
  indicatorId: string,
  getAccessToken?: GetToken,
  goalYear?: number,
  signal?: AbortSignal,
): Promise<StrategicIndicatorGoalHistoryResponse> {
  const searchParams = new URLSearchParams({
    indicator_id: indicatorId,
  });

  if (typeof goalYear === "number") {
    searchParams.set("goal_year", String(goalYear));
  }

  const response = await fetch(
    `${BASE_URL}/indicator-goals/history?${searchParams.toString()}`,
    {
      method: "GET",
      headers: buildHeaders(getAccessToken),
      signal,
    },
  );

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Failed to load goal history.");
  }

  return response.json();
}

export async function createStrategicIndicatorGoal(
  payload: CreateStrategicIndicatorGoalRequest,
  getAccessToken?: GetToken,
): Promise<{ id: string }> {
  const response = await fetch(`${BASE_URL}/indicator-goals`, {
    method: "POST",
    headers: buildHeaders(getAccessToken),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Failed to create indicator goal.");
  }

  return response.json();
}

export async function updateStrategicIndicatorGoal(
  goalId: string,
  payload: UpdateStrategicIndicatorGoalRequest,
  getAccessToken?: GetToken,
): Promise<{ id: string }> {
  const response = await fetch(`${BASE_URL}/indicator-goals/${goalId}`, {
    method: "PUT",
    headers: buildHeaders(getAccessToken),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Failed to update indicator goal.");
  }

  return response.json();
}

export async function activateStrategicIndicatorGoal(
  goalId: string,
  getAccessToken?: GetToken,
): Promise<{ id: string }> {
  const response = await fetch(`${BASE_URL}/indicator-goals/${goalId}/activate`, {
    method: "POST",
    headers: buildHeaders(getAccessToken),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Failed to activate indicator goal.");
  }

  return response.json();
}

export async function deactivateStrategicIndicatorGoal(
  goalId: string,
  getAccessToken?: GetToken,
): Promise<{ id: string }> {
  const response = await fetch(`${BASE_URL}/indicator-goals/${goalId}`, {
    method: "DELETE",
    headers: buildHeaders(getAccessToken),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Failed to deactivate indicator goal.");
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