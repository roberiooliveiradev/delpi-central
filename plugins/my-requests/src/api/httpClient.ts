import {
  getMyRequestsClientId,
  MY_REQUESTS_CLIENT_ID_HEADER,
} from "../app/myRequestsClientId";
import {
  humanizeApiErrorCode,
  isTechnicalErrorCode,
} from "../content/apiErrorMessages";

type RequestOptions = { signal?: AbortSignal };

const DELPI_CALLER_APP = "my-requests";

let accessTokenGetter: (() => string | undefined) | null = null;

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
    [MY_REQUESTS_CLIENT_ID_HEADER]: getMyRequestsClientId(),
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

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string | null;

  constructor(status: number, message: string, code: string | null = null) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
  }
}

async function parseError(response: Response, bodyText?: string): Promise<string> {
  const text = bodyText ?? (await readBodyText(response));
  if (looksLikeHtml(text, response.headers.get("content-type"))) {
    return "API de Minhas Solicitações indisponível. Verifique o serviço requests-api e o gateway.";
  }
  try {
    const body = JSON.parse(text) as {
      message?: string;
      detail?: string | unknown;
      data?: { message?: string; code?: string; field?: string };
    };
    const code =
      typeof body?.data?.code === "string" ? body.data.code.trim() : "";
    const field =
      typeof body?.data?.field === "string" ? body.data.field.trim() : null;
    const rawMessage =
      (typeof body?.message === "string" && body.message.trim()) ||
      (typeof body?.detail === "string" && body.detail.trim()) ||
      (typeof body?.data?.message === "string" && body.data.message.trim()) ||
      "";
    if (rawMessage) {
      if (isTechnicalErrorCode(rawMessage)) {
        return (
          humanizeApiErrorCode(rawMessage, { field }) ||
          humanizeApiErrorCode(code, { field }) ||
          rawMessage
        );
      }
      return rawMessage;
    }
    if (code) {
      return humanizeApiErrorCode(code, { field }) || code;
    }
  } catch {
    // ignore
  }
  if (response.status === 401) return "Sessão expirada. Faça login novamente.";
  if (response.status === 403) {
    return "Você não possui permissão para esta operação em Minhas Solicitações.";
  }
  if (response.status === 404) return "Solicitação não encontrada ou indisponível.";
  if (response.status === 502 || response.status === 503) {
    return "API de Minhas Solicitações indisponível. Tente novamente em instantes.";
  }
  return `Não foi possível concluir a operação (erro ${response.status}).`;
}

async function parseJson<T>(response: Response): Promise<T> {
  const text = await readBodyText(response);
  if (looksLikeHtml(text, response.headers.get("content-type"))) {
    throw new ApiClientError(response.status, await parseError(response, text));
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiClientError(response.status, "Resposta inválida da API (não é JSON).");
  }
}

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
    signal: options.signal,
  });
  if (!response.ok) {
    throw new ApiClientError(response.status, await parseError(response));
  }
  return parseJson<T>(response);
}

export async function httpPost<T>(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    signal: options.signal,
  });
  if (!response.ok) {
    throw new ApiClientError(response.status, await parseError(response));
  }
  return parseJson<T>(response);
}

export async function httpPatch<T>(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "PATCH",
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    signal: options.signal,
  });
  if (!response.ok) {
    throw new ApiClientError(response.status, await parseError(response));
  }
  return parseJson<T>(response);
}

export async function httpDelete<T>(
  url: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "DELETE",
    headers: authHeaders(),
    signal: options.signal,
  });
  if (!response.ok) {
    throw new ApiClientError(response.status, await parseError(response));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  const text = await readBodyText(response);
  if (!text.trim()) {
    return undefined as T;
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiClientError(response.status, "Resposta inválida da API (não é JSON).");
  }
}

export { DELPI_CALLER_APP };
