import {
  COMMERCIAL_CLIENT_ID_HEADER,
  getCommercialClientId,
} from "../app/commercialClientId";

type RequestOptions = {
  signal?: AbortSignal;
};

type JsonBody = Record<string, unknown> | unknown[];

export const COMMERCIAL_API_BASE = "/apps/commercial-api";

const DELPI_CALLER_APP = "commercial";

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

function formatErrorMessage(errorBody: unknown, fallback: string): string {
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

function buildHeaders(withJsonBody: boolean, includeClientId = false): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
  };
  if (withJsonBody) {
    headers["Content-Type"] = "application/json";
  }
  if (includeClientId && typeof window !== "undefined") {
    headers[COMMERCIAL_CLIENT_ID_HEADER] = getCommercialClientId();
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
    message = formatErrorMessage(errorBody, message);
  } catch {
    // mantém mensagem padrão
  }
  return message;
}

export function commercialApiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${COMMERCIAL_API_BASE}${normalized}`;
}

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
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
    headers: buildHeaders(body !== undefined, true),
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
  const response = await fetch(url, {
    method: "PUT",
    headers: buildHeaders(false, true),
    body: formData,
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json() as Promise<T>;
}

/** POST multipart (não define Content-Type — o browser preenche o boundary). */
export async function httpPostFormData<T>(
  url: string,
  formData: FormData,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: buildHeaders(false, true),
    body: formData,
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json() as Promise<T>;
}

export async function httpGetBlob(url: string, options: RequestOptions = {}): Promise<Blob> {
  const { blob } = await httpGetBlobWithMeta(url, options);
  return blob;
}

function filenameFromContentDisposition(header: string | null): string | null {
  if (!header) return null;
  const match = header.match(/filename=\"?([^\";]+)\"?/i);
  return match?.[1]?.trim() ?? null;
}

export async function httpGetBlobWithMeta(
  url: string,
  options: RequestOptions = {},
): Promise<{ blob: Blob; filename: string | null; contentType: string | null }> {
  const headers = buildHeaders(false);
  headers.Accept = "application/pdf,application/octet-stream,*/*";
  const response = await fetch(url, {
    method: "GET",
    headers,
    signal: options.signal,
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return {
    blob: await response.blob(),
    filename: filenameFromContentDisposition(response.headers.get("Content-Disposition")),
    contentType: response.headers.get("Content-Type"),
  };
}

export async function httpPostBlob(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<{ blob: Blob; filename: string | null; contentType: string | null }> {
  const headers = buildHeaders(true);
  headers.Accept = "application/pdf,application/octet-stream,*/*";
  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(body ?? {}),
    signal: options.signal,
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return {
    blob: await response.blob(),
    filename: filenameFromContentDisposition(response.headers.get("Content-Disposition")),
    contentType: response.headers.get("Content-Type"),
  };
}
