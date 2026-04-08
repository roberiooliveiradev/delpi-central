import type {
  StrategicIndicatorsSettingsResponse,
  StrategicIndicatorsSettingsUpdateRequest,
} from "../types/settings";

const BASE_URL = "/apps/api-delpi/strategic-indicators";

type GetToken = (() => string | undefined) | undefined;

function buildHeaders(getAccessToken?: GetToken): HeadersInit {
  const token = getAccessToken?.();

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function fetchStrategicIndicatorsSettings(
  getAccessToken?: GetToken,
  signal?: AbortSignal,
): Promise<StrategicIndicatorsSettingsResponse> {
  const response = await fetch(`${BASE_URL}/settings`, {
    method: "GET",
    headers: buildHeaders(getAccessToken),
    signal,
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao carregar configurações do módulo.");
  }

  return response.json();
}

export async function updateStrategicIndicatorsSettings(
  payload: StrategicIndicatorsSettingsUpdateRequest,
  getAccessToken?: GetToken,
): Promise<{ message: string }> {
  const response = await fetch(`${BASE_URL}/settings`, {
    method: "PUT",
    headers: buildHeaders(getAccessToken),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao salvar configurações do módulo.");
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