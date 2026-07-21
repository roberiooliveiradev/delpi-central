type RequestOptions = {
  signal?: AbortSignal;
};

const DELPI_CALLER_APP = "reports";

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

function formatApiDelpiErrorMessage(errorBody: unknown, fallback: string): string {
  if (!errorBody || typeof errorBody !== "object") {
    return fallback;
  }

  const record = errorBody as Record<string, unknown>;
  const base =
    (typeof record.message === "string" && record.message) ||
    (typeof record.detail === "string" && record.detail) ||
    fallback;
  const error = record.error;

  if (error && typeof error === "object") {
    const code = (error as { code?: unknown }).code;
    if (typeof code === "string" && code) {
      return `[${code}] ${base}`;
    }
  }

  return base;
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

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      message = formatApiDelpiErrorMessage(errorBody, message);
    } catch {
      // mantém mensagem padrão
    }
    throw new HttpRequestError(message, response.status);
  }

  return response.json() as Promise<T>;
}

export async function httpGet<T>(
  url: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
    signal: options.signal,
  });

  return parseJson<T>(response);
}

export async function httpSend<T>(
  method: "POST" | "PUT" | "PATCH" | "DELETE",
  url: string,
  body?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const headers = authHeaders();
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(url, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: options.signal,
  });
  return parseJson<T>(response);
}

export async function httpPost<T>(
  url: string,
  body?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  return httpSend<T>("POST", url, body, options);
}

export async function httpPut<T>(
  url: string,
  body?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  return httpSend<T>("PUT", url, body, options);
}

export async function httpPatch<T>(
  url: string,
  body?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  return httpSend<T>("PATCH", url, body, options);
}

export async function httpDelete<T>(
  url: string,
  options: RequestOptions = {},
): Promise<T> {
  return httpSend<T>("DELETE", url, undefined, options);
}
