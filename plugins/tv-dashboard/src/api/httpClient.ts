type RequestOptions = { signal?: AbortSignal; keepalive?: boolean };

const API_BASE = "/apps/tv-dashboard-api";
const DELPI_CALLER_APP = "tv-dashboard";

let accessTokenGetter: (() => string | undefined) | null = null;

export class HttpRequestError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "HttpRequestError";
    this.status = status;
  }
}

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

export function getAccessToken(): string | undefined {
  return accessTokenGetter?.();
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
  };
  const token = accessTokenGetter?.();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      const body = await response.json();
      if (body && typeof body === "object" && "message" in body) {
        message = String((body as { message: string }).message);
      }
    } catch {
      // noop
    }
    throw new HttpRequestError(message, response.status);
  }
  return response.json() as Promise<T>;
}

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, { method: "GET", headers: authHeaders(), signal: options.signal });
  return parseJson<T>(response);
}

export async function httpPost<T>(url: string, body: unknown, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: options.signal,
    keepalive: options.keepalive,
  });
  return parseJson<T>(response);
}

export async function httpPatch<T>(url: string, body: unknown, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "PATCH",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: options.signal,
    keepalive: options.keepalive,
  });
  return parseJson<T>(response);
}

export async function httpDelete<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, { method: "DELETE", headers: authHeaders(), signal: options.signal });
  return parseJson<T>(response);
}

export async function httpGetBlob(url: string): Promise<Blob> {
  const response = await fetch(url, { method: "GET", headers: authHeaders() });
  if (!response.ok) {
    throw new HttpRequestError(`Erro HTTP ${response.status}`, response.status);
  }
  return response.blob();
}

export async function httpPostForm<T>(url: string, form: FormData): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  return parseJson<T>(response);
}

export { API_BASE };
