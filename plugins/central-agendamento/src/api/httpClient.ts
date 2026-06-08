type RequestOptions = {
  signal?: AbortSignal;
};

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

const DELPI_CALLER_APP = "central-agendamento";

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

export function getAccessToken(): string | undefined {
  return accessTokenGetter?.();
}

function formatApiError(errorBody: unknown, status: number): string {
  if (!errorBody || typeof errorBody !== "object") {
    return `Erro HTTP ${status}`;
  }

  const body = errorBody as Record<string, unknown>;

  const base =
    (typeof body.message === "string" && body.message.trim() && body.message) ||
    (typeof body.detail === "string" && body.detail.trim() && body.detail) ||
    `Erro HTTP ${status}`;

  const error = body.error;
  if (error && typeof error === "object") {
    const code = (error as { code?: unknown }).code;
    if (typeof code === "string" && code) {
      return `[${code}] ${base}`;
    }
  }

  return base;
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      message = formatApiError(errorBody, response.status);
    } catch {
      // mantém mensagem padrão
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
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

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
    signal: options.signal,
  });
  return parseJson<T>(response);
}

export async function httpPost<T>(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: options.signal,
  });
  return parseJson<T>(response);
}

export async function httpPatch<T>(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "PATCH",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: options.signal,
  });
  return parseJson<T>(response);
}

export type { ApiEnvelope };
