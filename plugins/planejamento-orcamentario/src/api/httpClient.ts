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

export type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
  meta?: ApiDelpiResponseMeta;
  error?: ApiDelpiErrorPayload | null;
};

export class HttpRequestError extends Error {
  status: number;
  code?: string;
  meta?: Record<string, unknown>;

  constructor(
    message: string,
    status: number,
    options?: { code?: string; meta?: Record<string, unknown> },
  ) {
    super(message);
    this.name = "HttpRequestError";
    this.status = status;
    this.code = options?.code;
    this.meta = options?.meta;
  }
}

export function getHttpErrorCode(err: unknown): string | undefined {
  if (err instanceof HttpRequestError && err.code) return err.code;
  if (!err || typeof err !== "object") return undefined;
  const message = String((err as { message?: string }).message ?? "");
  const match = message.match(/^\[([^\]]+)\]\s*/);
  return match?.[1];
}

export function unwrapApiDelpiEnvelope<T>(
  response: ApiEnvelope<T>,
  fallbackMessage: string,
): T {
  if (response.success === false) {
    throw new Error(response.message?.trim() || fallbackMessage);
  }
  return response.data;
}

const DELPI_CALLER_APP = "planejamento-orcamentario";
const API_BASE = "/apps/api-delpi/planejamento-orcamentario";

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

function extractErrorExtras(errorBody: unknown): {
  code?: string;
  meta?: Record<string, unknown>;
} {
  if (!errorBody || typeof errorBody !== "object") return {};
  const body = errorBody as Record<string, unknown>;
  const error = body.error;
  let code: string | undefined;
  if (error && typeof error === "object") {
    const raw = (error as { code?: unknown }).code;
    if (typeof raw === "string" && raw) code = raw;
  }
  const meta =
    body.meta && typeof body.meta === "object"
      ? (body.meta as Record<string, unknown>)
      : undefined;
  return { code, meta };
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    let code: string | undefined;
    let meta: Record<string, unknown> | undefined;
    try {
      const errorBody = await response.json();
      message = formatApiError(errorBody, response.status);
      ({ code, meta } = extractErrorExtras(errorBody));
    } catch {
      // mantém mensagem padrão
    }
    throw new HttpRequestError(message, response.status, { code, meta });
  }
  return response.json() as Promise<T>;
}

function authHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
    ...extra,
  };
  const token = accessTokenGetter?.();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export function apiUrl(path: string): string {
  if (path.startsWith("http")) return path;
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (normalized.startsWith(API_BASE)) return normalized;
  return `${API_BASE}${normalized}`;
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
  body?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: body === undefined ? undefined : JSON.stringify(body),
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
    headers: authHeaders({ "Content-Type": "application/json" }),
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
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
    signal: options.signal,
  });
  return parseJson<T>(response);
}

export async function httpGetEnvelope<T>(
  path: string,
  fallbackMessage: string,
  options: RequestOptions = {},
): Promise<T> {
  const envelope = await httpGet<ApiEnvelope<T>>(apiUrl(path), options);
  return unwrapApiDelpiEnvelope(envelope, fallbackMessage);
}

export async function httpPostEnvelope<T>(
  path: string,
  body: unknown,
  fallbackMessage: string,
  options: RequestOptions = {},
): Promise<T> {
  const envelope = await httpPost<ApiEnvelope<T>>(apiUrl(path), body, options);
  return unwrapApiDelpiEnvelope(envelope, fallbackMessage);
}

export async function httpPutEnvelope<T>(
  path: string,
  body: unknown,
  fallbackMessage: string,
  options: RequestOptions = {},
): Promise<T> {
  const envelope = await httpPut<ApiEnvelope<T>>(apiUrl(path), body, options);
  return unwrapApiDelpiEnvelope(envelope, fallbackMessage);
}

export async function httpPatchEnvelope<T>(
  path: string,
  body: unknown,
  fallbackMessage: string,
  options: RequestOptions = {},
): Promise<T> {
  const envelope = await httpPatch<ApiEnvelope<T>>(apiUrl(path), body, options);
  return unwrapApiDelpiEnvelope(envelope, fallbackMessage);
}

/** Multipart: não definir Content-Type (boundary gerado pelo browser). */
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

export type UploadProgressCallback = (ratio: number) => void;

/**
 * Upload multipart com progresso (XHR).
 * `ratio` ∈ [0, 1]; se o browser não reportar, fica em 0 até concluir.
 */
export function httpPostFormWithProgress<T>(
  url: string,
  formData: FormData,
  options: RequestOptions & { onProgress?: UploadProgressCallback } = {},
): Promise<T> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url);
    const headers = authHeaders();
    Object.entries(headers).forEach(([key, value]) => {
      xhr.setRequestHeader(key, value);
    });
    xhr.responseType = "json";

    if (options.signal) {
      if (options.signal.aborted) {
        reject(new DOMException("Aborted", "AbortError"));
        return;
      }
      options.signal.addEventListener(
        "abort",
        () => {
          xhr.abort();
          reject(new DOMException("Aborted", "AbortError"));
        },
        { once: true },
      );
    }

    xhr.upload.onprogress = (event) => {
      if (!options.onProgress) return;
      if (event.lengthComputable && event.total > 0) {
        options.onProgress(event.loaded / event.total);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve((xhr.response ?? {}) as T);
        return;
      }
      let message = `Erro HTTP ${xhr.status}`;
      let code: string | undefined;
      let meta: Record<string, unknown> | undefined;
      try {
        message = formatApiError(xhr.response, xhr.status);
        ({ code, meta } = extractErrorExtras(xhr.response));
      } catch {
        // mantém mensagem padrão
      }
      reject(new HttpRequestError(message, xhr.status, { code, meta }));
    };

    xhr.onerror = () => {
      reject(new HttpRequestError("Falha de rede no upload.", 0));
    };

    xhr.send(formData);
  });
}

export async function httpPostFormEnvelope<T>(
  path: string,
  formData: FormData,
  fallbackMessage: string,
  options: RequestOptions & { onProgress?: UploadProgressCallback } = {},
): Promise<T> {
  const envelope = await httpPostFormWithProgress<ApiEnvelope<T>>(
    apiUrl(path),
    formData,
    options,
  );
  return unwrapApiDelpiEnvelope(envelope, fallbackMessage);
}

export async function downloadAuthenticatedFile(path: string): Promise<Blob> {
  const result = await downloadAuthenticatedBinary(path);
  return result.blob;
}

export type AuthenticatedBinaryResult = {
  blob: Blob;
  filename: string | null;
};

function parseContentDispositionFilename(header: string | null): string | null {
  if (!header) return null;
  const utfMatch = header.match(/filename\*\s*=\s*UTF-8''([^;]+)/i);
  if (utfMatch?.[1]) {
    try {
      return decodeURIComponent(utfMatch[1].trim().replace(/^"|"$/g, ""));
    } catch {
      return utfMatch[1].trim().replace(/^"|"$/g, "");
    }
  }
  const plainMatch = header.match(/filename\s*=\s*("?)([^";]+)\1/i);
  return plainMatch?.[2]?.trim() || null;
}

/** Download autenticado com nome de arquivo (Content-Disposition) e código de erro. */
export async function downloadAuthenticatedBinary(
  path: string,
): Promise<AuthenticatedBinaryResult> {
  const response = await fetch(apiUrl(path), {
    method: "GET",
    headers: authHeaders({ Accept: "*/*" }),
  });

  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    let code: string | undefined;
    let meta: Record<string, unknown> | undefined;
    try {
      const errorBody = await response.json();
      message = formatApiError(errorBody, response.status);
      ({ code, meta } = extractErrorExtras(errorBody));
    } catch {
      // mantém mensagem padrão
    }
    throw new HttpRequestError(message, response.status, { code, meta });
  }

  return {
    blob: await response.blob(),
    filename: parseContentDispositionFilename(response.headers.get("Content-Disposition")),
  };
}
