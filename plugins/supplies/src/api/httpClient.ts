import { formatApiErrorBody, resolveHttpErrorMessage } from "./httpErrorMessage";

type RequestOptions = {
  signal?: AbortSignal;
};

type JsonBody = Record<string, unknown> | unknown[];

export const SUPPLIES_API_BASE = "/apps/supplies-api";

const DELPI_CALLER_APP = "supplies";

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
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

export class ApiRequestError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly outcome?: string;
  readonly retryAfter?: number;

  constructor(
    message: string,
    options: {
      status: number;
      code?: string;
      outcome?: string;
      retryAfter?: number;
    },
  ) {
    super(message);
    this.name = "ApiRequestError";
    this.status = options.status;
    this.code = options.code;
    this.outcome = options.outcome;
    this.retryAfter = options.retryAfter;
  }
}

async function parseError(response: Response): Promise<ApiRequestError> {
  const status = response.status;
  let rawFromBody: string | null = null;
  let code: string | undefined;
  let outcome: string | undefined;
  try {
    const text = await response.text();
    if (text.trim()) {
      try {
        const errorBody: unknown = JSON.parse(text);
        rawFromBody = formatApiErrorBody(errorBody, text);
        if (errorBody && typeof errorBody === "object") {
          const body = errorBody as Record<string, unknown>;
          if (typeof body.code === "string") code = body.code;
          if (typeof body.outcome === "string") outcome = body.outcome;
        }
      } catch {
        rawFromBody = text;
      }
    }
  } catch {
    rawFromBody = null;
  }
  const retryAfterHeader = response.headers.get("Retry-After");
  const retryAfter =
    retryAfterHeader !== null && /^\d+$/.test(retryAfterHeader.trim())
      ? Number(retryAfterHeader.trim())
      : undefined;
  return new ApiRequestError(resolveHttpErrorMessage(status, rawFromBody), {
    status,
    code,
    outcome,
    retryAfter,
  });
}

export function suppliesApiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${SUPPLIES_API_BASE}${normalized}`;
}

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: buildHeaders(false),
    signal: options.signal,
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  return response.json() as Promise<T>;
}

export async function httpGetBlob(url: string, options: RequestOptions = {}): Promise<Blob> {
  const response = await fetch(url, {
    method: "GET",
    headers: buildHeaders(false),
    signal: options.signal,
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  return response.blob();
}

export async function httpPost<T>(
  url: string,
  body?: JsonBody,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: buildHeaders(body !== undefined),
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal: options.signal,
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function httpPut<T>(
  url: string,
  body?: JsonBody,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "PUT",
    headers: buildHeaders(body !== undefined),
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal: options.signal,
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function httpPatch<T>(
  url: string,
  body?: JsonBody,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "PATCH",
    headers: buildHeaders(body !== undefined),
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal: options.signal,
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
