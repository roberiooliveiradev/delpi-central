type RequestOptions = { signal?: AbortSignal };

const DELPI_CALLER_APP = "mural-acessos";

export class HttpRequestError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "HttpRequestError";
    this.status = status;
  }
}

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

export function unwrapApiDelpiEnvelope<T>(
  payload: ApiEnvelope<T> | T,
  fallback: string,
): T {
  if (payload && typeof payload === "object" && "success" in payload && "data" in payload) {
    const envelope = payload as ApiEnvelope<T>;
    if (envelope.success === false) {
      throw new HttpRequestError(envelope.message || fallback, 422);
    }
    return envelope.data;
  }
  return payload as T;
}

function formatApiDelpiErrorMessage(errorBody: unknown, fallback: string): string {
  if (!errorBody || typeof errorBody !== "object") {
    return fallback;
  }
  const record = errorBody as Record<string, unknown>;
  if (typeof record.message === "string" && record.message) {
    return record.message;
  }
  if (typeof record.detail === "string" && record.detail) {
    return record.detail;
  }
  return fallback;
}

function authHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
    ...extra,
  };
  const token = accessTokenGetter?.();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function parseJson<T>(response: Response, fallback: string): Promise<T> {
  if (!response.ok) {
    let message = fallback;
    try {
      const errorBody = await response.json();
      message = formatApiDelpiErrorMessage(errorBody, fallback);
    } catch {
      message = `Erro HTTP ${response.status}`;
    }
    throw new HttpRequestError(message, response.status);
  }
  return response.json() as Promise<T>;
}

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
    signal: options.signal,
  });
  return parseJson<T>(response, "Não foi possível carregar os dados.");
}

export async function httpPost<T>(
  url: string,
  body?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: authHeaders(body !== undefined ? { "Content-Type": "application/json" } : undefined),
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal: options.signal,
  });
  return parseJson<T>(response, "Não foi possível salvar.");
}

export async function httpPut<T>(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
    signal: options.signal,
  });
  return parseJson<T>(response, "Não foi possível atualizar.");
}

export async function httpDelete<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "DELETE",
    headers: authHeaders(),
    signal: options.signal,
  });
  return parseJson<T>(response, "Não foi possível remover.");
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
  return parseJson<T>(response, "Não foi possível enviar a imagem.");
}

export async function httpGetBlob(url: string, options: RequestOptions = {}): Promise<Blob> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
    signal: options.signal,
  });
  if (!response.ok) {
    throw new HttpRequestError(`Erro HTTP ${response.status}`, response.status);
  }
  return response.blob();
}
