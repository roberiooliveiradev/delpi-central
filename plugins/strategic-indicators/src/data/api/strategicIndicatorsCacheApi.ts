import { clearAllStrategicIndicatorsCache } from "../cache/strategicIndicatorsReadCache";
import { STRATEGIC_INDICATORS_API_BASE } from "./strategicIndicatorsApiBase";

const BASE_URL = STRATEGIC_INDICATORS_API_BASE;

type GetToken = (() => string | undefined) | undefined;

function buildHeaders(getAccessToken?: GetToken): HeadersInit {
  const token = getAccessToken?.();

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function invalidateStrategicIndicatorsCache(
  getAccessToken?: GetToken,
): Promise<void> {
  const response = await fetch(`${BASE_URL}/cache/invalidate`, {
    method: "POST",
    headers: buildHeaders(getAccessToken),
  });

  if (!response.ok) {
    throw new Error(
      `Falha ao invalidar cache do backend (${response.status}).`,
    );
  }

  clearAllStrategicIndicatorsCache();
}
