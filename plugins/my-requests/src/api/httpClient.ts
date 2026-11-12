import {
  getMyRequestsClientId,
  MY_REQUESTS_CLIENT_ID_HEADER,
} from "../app/myRequestsClientId";
import {
  humanizeApiErrorCode,
  isTechnicalErrorCode,
} from "../content/apiErrorMessages";

type RequestOptions = { signal?: AbortSignal; headers?: Record<string, string> };

const DELPI_CALLER_APP = "my-requests";

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

export function getAccessToken(): string | undefined {
  return accessTokenGetter?.();
}

export function authHeaders(): Record<string, string> {
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
  /** Campos identificáveis do envelope de erro (``data.fields``) —
   * usado pela validação contextual FIX-12 quando o contrato
   * identifica o campo responsável. */
  readonly fields?: Record<string, string>;

  constructor(
    status: number,
    message: string,
    code: string | null = null,
    fields?: Record<string, string>,
  ) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

type ParsedError = { message: string; fields?: Record<string, string> };

async function errorFromResponse(
  response: Response,
  bodyText?: string,
): Promise<ApiClientError> {
  const { message, fields } = await parseErrorDetails(response, bodyText);
  return new ApiClientError(response.status, message, null, fields);
}

async function parseErrorDetails(
  response: Response,
  bodyText?: string,
): Promise<ParsedError> {
  const text = bodyText ?? (await readBodyText(response));
  if (looksLikeHtml(text, response.headers.get("content-type"))) {
    return {
      message:
        "API de Minhas Solicitações indisponível. Verifique o serviço requests-api e o gateway.",
    };
  }
  let fields: Record<string, string> | undefined;
  try {
    const body = JSON.parse(text) as {
      message?: string;
      detail?: string | unknown;
      data?: {
        message?: string;
        code?: string;
        field?: string;
        fields?: Record<string, string>;
      };
    };
    if (
      body?.data?.fields &&
      typeof body.data.fields === "object" &&
      !Array.isArray(body.data.fields)
    ) {
      fields = Object.fromEntries(
        Object.entries(body.data.fields).map(([k, v]) => [k, String(v)]),
      );
    }
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
        return {
          message:
            humanizeApiErrorCode(rawMessage, { field }) ||
            humanizeApiErrorCode(code, { field }) ||
            rawMessage,
          fields,
        };
      }
      return { message: rawMessage, fields };
    }
    if (code) {
      return { message: humanizeApiErrorCode(code, { field }) || code, fields };
    }
  } catch {
    // ignore
  }
  if (response.status === 401) {
    return { message: "Sessão expirada. Faça login novamente." };
  }
  if (response.status === 403) {
    return {
      message:
        "Você não possui permissão para esta operação em Minhas Solicitações.",
    };
  }
  if (response.status === 404) {
    return { message: "Solicitação não encontrada ou indisponível." };
  }
  if (response.status === 502 || response.status === 503) {
    return {
      message:
        "API de Minhas Solicitações indisponível. Tente novamente em instantes.",
    };
  }
  return {
    message: `Não foi possível concluir a operação (erro ${response.status}).`,
  };
}

async function parseJson<T>(response: Response): Promise<T> {
  const text = await readBodyText(response);
  if (looksLikeHtml(text, response.headers.get("content-type"))) {
    throw await errorFromResponse(response, text);
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
    headers: { ...authHeaders(), ...(options.headers || {}) },
    signal: options.signal,
  });
  if (!response.ok) {
    throw await errorFromResponse(response);
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
      ...(options.headers || {}),
    },
    body: JSON.stringify(body),
    signal: options.signal,
  });
  if (!response.ok) {
    throw await errorFromResponse(response);
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
      ...(options.headers || {}),
    },
    body: JSON.stringify(body),
    signal: options.signal,
  });
  if (!response.ok) {
    throw await errorFromResponse(response);
  }
  return parseJson<T>(response);
}

export async function httpDelete<T>(
  url: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "DELETE",
    headers: { ...authHeaders(), ...(options.headers || {}) },
    signal: options.signal,
  });
  if (!response.ok) {
    throw await errorFromResponse(response);
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
