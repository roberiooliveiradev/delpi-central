export const TRANSFORMOMETRO_API_BASE =
  import.meta.env.VITE_TRANSFORMOMETRO_API_BASE?.trim() ||
  "/apps/transformometro-api/transformometro";

export function buildAuthHeaders(getAccessToken?: () => string | undefined): HeadersInit {
  const token = getAccessToken?.();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}
