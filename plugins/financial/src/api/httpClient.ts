import { FINANCIAL_API_BASE } from "../constants/routes";

type RequestOptions = {
  signal?: AbortSignal;
  accept?: string;
};

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

const DELPI_CALLER_APP = "financial";
const RETRYABLE_HTTP_STATUSES = new Set([502, 503, 504]);
const HTTP_GET_MAX_ATTEMPTS = 3;

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

export function unwrapEnvelope<T>(response: ApiEnvelope<T>, fallbackMessage: string): T {
  if (response.success === false) {
    throw new Error(response.message?.trim() || fallbackMessage);
  }
  return response.data;
}

function authHeaders(accept = "application/json"): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: accept,
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

async function readErrorMessage(response: Response): Promise<string> {
  try {
    return formatApiError(await response.json(), response.status);
  } catch {
    return `Erro HTTP ${response.status}`;
  }
}

/** GET autenticado com o mesmo retry de 502/503/504 usado pelo JSON. */
async function httpGetResponse(url: string, options: RequestOptions = {}): Promise<Response> {
  let lastMessage = "Erro ao consultar a API.";

  for (let attempt = 1; attempt <= HTTP_GET_MAX_ATTEMPTS; attempt += 1) {
    const response = await fetch(url, {
      method: "GET",
      headers: authHeaders(options.accept),
      signal: options.signal,
    });

    if (!response.ok) {
      const message = await readErrorMessage(response);
      lastMessage = message;
      if (RETRYABLE_HTTP_STATUSES.has(response.status) && attempt < HTTP_GET_MAX_ATTEMPTS) {
        await delay(250 * attempt);
        continue;
      }
      throw new Error(message);
    }

    return response;
  }

  throw new Error(lastMessage);
}

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await httpGetResponse(url, options);
  return response.json() as Promise<T>;
}

export type BlobDownload = {
  blob: Blob;
  filename: string | null;
};

export function filenameFromContentDisposition(header: string | null): string | null {
  if (!header) return null;
  const encoded = /filename\*=UTF-8''([^;]+)/i.exec(header);
  const plain = /filename="?([^";]+)"?/i.exec(header);
  const raw = (encoded?.[1] ?? plain?.[1] ?? "").trim();
  if (!raw) return null;
  try {
    return decodeURIComponent(raw);
  } catch {
    return raw;
  }
}

export async function httpGetBlob(url: string, options: RequestOptions = {}): Promise<BlobDownload> {
  const response = await httpGetResponse(url, {
    ...options,
    accept: options.accept ?? "application/pdf, application/json",
  });
  return {
    blob: await response.blob(),
    filename: filenameFromContentDisposition(response.headers.get("Content-Disposition")),
  };
}

export async function downloadAuthenticatedBlob(
  url: string,
  fallbackFilename: string,
  options: RequestOptions = {},
): Promise<void> {
  const downloaded = await httpGetBlob(url, options);
  const objectUrl = URL.createObjectURL(downloaded.blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = downloaded.filename || fallbackFilename;
    anchor.rel = "noopener";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

export function financialApiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${FINANCIAL_API_BASE}${normalized}`;
}
