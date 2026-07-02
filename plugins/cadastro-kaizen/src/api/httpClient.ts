type RequestOptions = {
  signal?: AbortSignal;
};

type ApiDelpiResponseMeta = {
  dataVersion?: string;
  operationId?: string;
  entity?: string;
  shape?: string;
  pagination?: Record<string, unknown>;
  fields?: Record<string, string>;
};

type ApiDelpiErrorPayload = {
  code?: string;
  recoverable?: boolean;
};

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
  meta?: ApiDelpiResponseMeta;
  error?: ApiDelpiErrorPayload | null;
};

export function unwrapApiDelpiEnvelope<T>(
  response: ApiEnvelope<T>,
  fallbackMessage: string,
): T {
  if (response.success === false) {
    throw new Error(response.message?.trim() || fallbackMessage);
  }
  return response.data;
}

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
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
      const errorBody = await response.json();
      message = formatApiError(errorBody, response.status);
    } catch {
      // mantém mensagem padrão
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

const DELPI_CALLER_APP = "cadastro-kaizen";

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

export async function httpPut<T>(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "PUT",
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

export async function httpPostForm<T>(
  url: string,
  form: FormData,
  options: RequestOptions = {},
): Promise<T> {
  // Sem Content-Type manual: o browser define o boundary do multipart.
  const response = await fetch(url, {
    method: "POST",
    headers: authHeaders(),
    body: form,
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

export function authBearerHeader(): Record<string, string> {
  return authHeaders();
}

export type { ApiEnvelope };
