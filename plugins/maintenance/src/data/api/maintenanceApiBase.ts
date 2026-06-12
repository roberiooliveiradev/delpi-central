export const MAINTENANCE_API_BASE =
  import.meta.env.VITE_MAINTENANCE_API_BASE?.trim() || "/apps/maintenance-api/maintenance";

export function buildAuthHeaders(getAccessToken?: () => string | undefined): HeadersInit {
  const token = getAccessToken?.();
  if (!token) return {};
  return { Authorization: token.startsWith("Bearer ") ? token : `Bearer ${token}` };
}

export type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

export async function maintenanceFetch<T>(
  path: string,
  options: RequestInit & { getAccessToken?: () => string | undefined } = {},
): Promise<T> {
  const { getAccessToken, ...init } = options;
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  const token = getAccessToken?.();
  if (token) {
    headers.set("Authorization", token.startsWith("Bearer ") ? token : `Bearer ${token}`);
  }

  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${MAINTENANCE_API_BASE}${path}`, {
    ...init,
    headers,
  });

  const body = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || !body.success) {
    throw new Error(body.message || "Falha na requisição.");
  }

  return body.data;
}
