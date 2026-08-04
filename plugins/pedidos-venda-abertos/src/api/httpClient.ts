type RequestOptions = {
  signal?: AbortSignal;
};

type JsonBody = Record<string, unknown> | unknown[];

const DELPI_CALLER_APP = "pedidos-venda-abertos";

let accessTokenGetter: (() => string | undefined) | null = null;

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

function buildHeaders(withJsonBody: boolean): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
  };
  if (withJsonBody) {
    headers["Content-Type"] = "application/json";
  }
  const token = accessTokenGetter?.();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function parseError(response: Response): Promise<string> {
  let message = `Erro HTTP ${response.status}`;
  try {
    const errorBody = await response.json();
    message = formatApiDelpiErrorMessage(errorBody, message);
  } catch {
    // mantém mensagem padrão
  }
  return message;
}

export async function httpGet<T>(
  url: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: buildHeaders(false),
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json() as Promise<T>;
}

async function httpJson<T>(
  method: string,
  url: string,
  body?: JsonBody,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: buildHeaders(body !== undefined),
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function httpPost<T>(url: string, body?: JsonBody, options?: RequestOptions) {
  return httpJson<T>("POST", url, body, options);
}

export function httpPut<T>(url: string, body?: JsonBody, options?: RequestOptions) {
  return httpJson<T>("PUT", url, body, options);
}

export function httpPatch<T>(url: string, body?: JsonBody, options?: RequestOptions) {
  return httpJson<T>("PATCH", url, body, options);
}

export function httpDelete<T>(url: string, options?: RequestOptions) {
  return httpJson<T>("DELETE", url, undefined, options);
}

/** PUT multipart (não define Content-Type — o browser preenche o boundary). */
export async function httpPutFormData<T>(
  url: string,
  formData: FormData,
  options: RequestOptions = {},
): Promise<T> {
  const headers = buildHeaders(false);
  const response = await fetch(url, {
    method: "PUT",
    headers,
    body: formData,
    signal: options.signal,
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json() as Promise<T>;
}

/** GET binário autenticado (logos). */
export async function httpGetBlob(
  url: string,
  options: RequestOptions = {},
): Promise<Blob> {
  const response = await fetch(url, {
    method: "GET",
    headers: buildHeaders(false),
    signal: options.signal,
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.blob();
}
