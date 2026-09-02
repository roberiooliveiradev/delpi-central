import { PP_HELP } from "../content/helpTooltips";

type RequestOptions = { signal?: AbortSignal };

const DELPI_CALLER_APP = "production-pulse";
export const PRODUCTION_PULSE_API_BASE = "/apps/production-pulse-api";

let accessTokenGetter: (() => string | undefined) | null = null;

export class ProductionPulseRequestError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ProductionPulseRequestError";
    this.status = status;
    this.code = code;
  }
}

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

export function getAccessToken(): string | undefined {
  return accessTokenGetter?.();
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
  };
  const token = accessTokenGetter?.();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function readBodyText(response: Response): Promise<string> {
  try {
    return await response.text();
  } catch {
    return "";
  }
}

function looksLikeHtml(body: string, contentType: string | null): boolean {
  const type = (contentType || "").toLowerCase();
  if (type.includes("text/html")) return true;
  const trimmed = body.trimStart().toLowerCase();
  return trimmed.startsWith("<!doctype") || trimmed.startsWith("<html");
}

type ParsedApiErrorBody = {
  message?: string;
  code?: string;
};

function parseApiErrorBody(text: string): ParsedApiErrorBody | null {
  try {
    const body = JSON.parse(text) as {
      message?: string;
      error?: { message?: string; code?: string };
    };
    return {
      message: body?.error?.message ?? body?.message,
      code: body?.error?.code,
    };
  } catch {
    return null;
  }
}

async function parseError(response: Response, bodyText?: string): Promise<string> {
  const text = bodyText ?? (await readBodyText(response));
  if (looksLikeHtml(text, response.headers.get("content-type"))) {
    return PP_HELP.apiErrors.apiUnavailable;
  }

  const parsed = parseApiErrorBody(text);
  if (parsed?.message) return parsed.message;

  if (response.status === 401) return "Sessão expirada. Faça login novamente.";
  if (response.status === 403) return "Você não tem permissão para esta operação.";
  if (response.status === 502 || response.status === 503) {
    return PP_HELP.apiErrors.apiUnavailable;
  }
  return `Erro HTTP ${response.status}`;
}

async function buildRequestError(response: Response, bodyText?: string): Promise<ProductionPulseRequestError> {
  const text = bodyText ?? (await readBodyText(response));
  const parsed = parseApiErrorBody(text);
  const message = await parseError(response, text);
  return new ProductionPulseRequestError(message, response.status, parsed?.code);
}

async function parseJson<T>(response: Response): Promise<T> {
  const text = await readBodyText(response);
  if (looksLikeHtml(text, response.headers.get("content-type"))) {
    throw await buildRequestError(response, text);
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error("Resposta inválida da API (não é JSON).");
  }
}

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
    signal: options.signal,
  });
  if (!response.ok) throw await buildRequestError(response);
  return parseJson<T>(response);
}

export async function httpJson<T>(
  method: string,
  url: string,
  body?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const headers = authHeaders();
  headers["Content-Type"] = "application/json";
  const response = await fetch(url, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: options.signal,
  });
  if (!response.ok) throw await buildRequestError(response);
  return parseJson<T>(response);
}
