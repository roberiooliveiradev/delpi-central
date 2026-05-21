import {
  TRANSFORMOMETRO_API_BASE,
  buildAuthHeaders,
} from "./transformometroApiBase";

export type HealthResponse = {
  status: string;
  module?: string;
  phase?: string;
};

export async function fetchTransformometroHealth(
  getAccessToken?: () => string | undefined
): Promise<HealthResponse> {
  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}/health`, {
    headers: buildAuthHeaders(getAccessToken),
  });

  if (!response.ok) {
    throw new Error(`Health check falhou (${response.status})`);
  }

  return response.json() as Promise<HealthResponse>;
}
