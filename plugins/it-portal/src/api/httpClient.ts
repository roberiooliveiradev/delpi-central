/** Única origem de dados do MFE: a BFF do Portal de TI. */
export const IT_PORTAL_API_BASE = "/apps/it-portal-api";

const DELPI_CALLER_APP = "it-portal";

const HTML_OR_GATEWAY_MARKERS = ["<!doctype", "<html", "bad gateway", "cloudflare", "cf-ray"];

export const HTTP_ERROR_MESSAGES = {
  401: "Sua sessão expirou. Entre novamente.",
  403: "Você não tem permissão para esta ação.",
  503: "Serviço temporariamente indisponível. Tente novamente em instantes.",
  gateway: "Serviço temporariamente indisponível. Tente novamente.",
  network: "Não foi possível conectar ao Portal de TI. Verifique sua conexão.",
  fallback: (status: number) => `Não foi possível concluir a operação (${status}).`,
} as const;

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

export type FieldErrors = Record<string, string>;

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly fieldErrors: FieldErrors;

  constructor(status: number, message: string, code: string | null = null, fieldErrors: FieldErrors = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fieldErrors = fieldErrors;
  }
}

type Envelope<T> = { success: boolean; message: string; data: T };

function buildHeaders(withBody: boolean): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
  };
  if (withBody) headers["Content-Type"] = "application/json";
  const token = accessTokenGetter?.();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

function looksLikeHtmlNoise(text: string): boolean {
  const normalized = text.trim().toLowerCase();
  return HTML_OR_GATEWAY_MARKERS.some((marker) => normalized.includes(marker));
}

/**
 * Mensagem segura para a UI: usa a `message` do envelope da BFF; respostas do
 * middleware (`detail` em inglês) e páginas de gateway caem no texto padrão.
 */
async function parseError(response: Response): Promise<ApiError> {
  const status = response.status;
  let message: string | null = null;
  let code: string | null = null;
  let fieldErrors: FieldErrors = {};
  try {
    const text = await response.text();
    if (text.trim() && !looksLikeHtmlNoise(text)) {
      const body = JSON.parse(text) as Record<string, unknown>;
      if (typeof body.message === "string" && body.message.trim()) message = body.message;
      const error = (body.data as { error?: { code?: unknown; details?: { fields?: unknown } } } | null)?.error;
      if (error && typeof error.code === "string") code = error.code;
      const fields = error?.details?.fields;
      if (fields && typeof fields === "object") fieldErrors = fields as FieldErrors;
    }
  } catch {
    message = null;
  }
  if (status >= 502 && status <= 504 && !message) message = HTTP_ERROR_MESSAGES.gateway;
  if (!message) {
    message =
      status === 401 || status === 403 || status === 503
        ? HTTP_ERROR_MESSAGES[status]
        : HTTP_ERROR_MESSAGES.fallback(status);
  }
  return new ApiError(status, message, code, fieldErrors);
}

export type QueryValue = string | number | boolean | null | undefined | readonly string[];

export function apiUrl(path: string, query?: Record<string, QueryValue>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      value.forEach((item) => params.append(key, item));
    } else {
      params.set(key, String(value));
    }
  }
  const search = params.toString();
  return `${IT_PORTAL_API_BASE}${path}${search ? `?${search}` : ""}`;
}

async function request<T>(method: string, url: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers: buildHeaders(body !== undefined),
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(0, HTTP_ERROR_MESSAGES.network, "network_error");
  }
  if (!response.ok) throw await parseError(response);
  const envelope = (await response.json()) as Envelope<T>;
  return envelope.data;
}

export function apiGet<T>(url: string, signal?: AbortSignal): Promise<T> {
  return request<T>("GET", url, undefined, signal);
}

export function apiPost<T>(url: string, body: unknown): Promise<T> {
  return request<T>("POST", url, body);
}

export function apiPut<T>(url: string, body: unknown): Promise<T> {
  return request<T>("PUT", url, body);
}
