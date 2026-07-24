import { getTransformometroClientId } from "../../utils/clientId";

export const TRANSFORMOMETRO_API_BASE =
  import.meta.env.VITE_TRANSFORMOMETRO_API_BASE?.trim() ||
  "/apps/transformometro-api/transformometro";

/** Header lido pela API para actorClientId no evento WS (anti-eco por aba). */
export const TRANSFORMOMETRO_CLIENT_ID_HEADER = "X-Transformometro-Client-Id";

export function buildAuthHeaders(getAccessToken?: () => string | undefined): HeadersInit {
  const headers: Record<string, string> = {
    [TRANSFORMOMETRO_CLIENT_ID_HEADER]: getTransformometroClientId(),
  };
  const token = getAccessToken?.();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}
