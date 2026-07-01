type RequestOptions = {
  signal?: AbortSignal;
};

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

export function unwrapEnvelope<T>(response: ApiEnvelope<T>, fallbackMessage: string): T {
  if (response.success === false) {
    throw new Error(response.message?.trim() || fallbackMessage);
  }
  return response.data;
}

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

const DELPI_CALLER_APP = "customer-experience";

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
  if (typeof body.detail === "string" && body.detail.trim()) {
    return body.detail;
  }
  return `Erro HTTP ${status}`;
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      message = formatApiError(await response.json(), response.status);
    } catch {
      // mantém mensagem padrão
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
    signal: options.signal,
  });
  return parseJson<T>(response);
}

export async function httpPostForm<T>(
  url: string,
  formData: FormData,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
    signal: options.signal,
  });
  return parseJson<T>(response);
}

export async function httpPost<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: authHeaders(),
    signal: options.signal,
  });
  return parseJson<T>(response);
}

export async function httpPatchForm<T>(
  url: string,
  formData: FormData,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "PATCH",
    headers: authHeaders(),
    body: formData,
    signal: options.signal,
  });
  return parseJson<T>(response);
}

export async function httpDelete<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "DELETE",
    headers: authHeaders(),
    signal: options.signal,
  });
  return parseJson<T>(response);
}

export async function httpDownloadBlob(url: string, options: RequestOptions = {}): Promise<Blob> {
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
      // mantém mensagem padrão
    }
    throw new Error(message);
  }
  return response.blob();
}

export type { ApiEnvelope };
