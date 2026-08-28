type RequestOptions = {
  signal?: AbortSignal;
};

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

export const PPC_API_BASE = "/apps/production-control-api";
const DELPI_CALLER_APP = "production-control";

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

/** Token atual (JWT) — usado só para UI local (ex.: primeiro nome no loading). */
export function peekAccessToken(): string | undefined {
  return accessTokenGetter?.();
}

export function unwrapEnvelope<T>(response: ApiEnvelope<T>, fallbackMessage: string): T {
  if (response.success === false) {
    throw new Error(response.message?.trim() || fallbackMessage);
  }
  return response.data;
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
  };
  const token = accessTokenGetter?.();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

function formatApiError(errorBody: unknown, status: number): string {
  if (!errorBody || typeof errorBody !== "object") {
    return `Erro HTTP ${status}`;
  }
  const body = errorBody as Record<string, unknown>;
  if (typeof body.message === "string" && body.message.trim()) {
    return body.message;
  }
  return `Erro HTTP ${status}`;
}

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
    signal: options.signal,
  });
  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      message = formatApiError(await response.json(), response.status);
    } catch {
      // keep default
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function httpGetBlob(url: string, options: RequestOptions = {}): Promise<Blob> {
  const response = await fetch(url, {
    method: "GET",
    headers: {
      ...authHeaders(),
      Accept: "application/pdf",
    },
    signal: options.signal,
  });
  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      message = formatApiError(await response.json(), response.status);
    } catch {
      // keep default
    }
    throw new Error(message);
  }
  return response.blob();
}

export async function httpPost<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
    },
    signal: options.signal,
  });
  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      message = formatApiError(await response.json(), response.status);
    } catch {
      // keep default
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function httpPatch<T>(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "PATCH",
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    signal: options.signal,
  });
  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      message = formatApiError(await response.json(), response.status);
    } catch {
      // keep default
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export function ppcApiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${PPC_API_BASE}${normalized}`;
}
