import { ApiClientError, type ApiErrorKind } from "../types/api";

const DELPI_CALLER_APP = "materiais-terceiros";

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

export function getAccessToken(): string | undefined {
  return accessTokenGetter?.();
}

type ParsedApiError = {
  message: string;
  code?: string;
};

function formatApiDelpiErrorMessage(errorBody: unknown, fallback: string): ParsedApiError {
  if (!errorBody || typeof errorBody !== "object") {
    return { message: fallback };
  }

  const record = errorBody as Record<string, unknown>;
  const base =
    (typeof record.message === "string" && record.message) ||
    (typeof record.detail === "string" && record.detail) ||
    fallback;

  const error = record.error;
  if (error && typeof error === "object") {
    const nested = error as { code?: unknown; message?: unknown };
    const code = typeof nested.code === "string" ? nested.code : undefined;
    const nestedMessage =
      typeof nested.message === "string" && nested.message ? nested.message : base;
    return { message: code ? `[${code}] ${nestedMessage}` : nestedMessage, code };
  }

  return { message: base };
}

function classifyHttpError(status: number, parsed: ParsedApiError, context?: string): never {
  const options = { code: parsed.code, context };

  if (status === 401) {
    throw new ApiClientError(
      "É necessário autenticar novamente para continuar.",
      status,
      "auth",
      { ...options, retryable: false },
    );
  }

  if (status === 403) {
    throw new ApiClientError(
      parsed.message ||
        "Você não possui permissão para consultar materiais de terceiros ou a filial solicitada.",
      status,
      "forbidden",
      { ...options, retryable: false },
    );
  }

  if (status === 400) {
    throw new ApiClientError(
      parsed.message || "Parâmetros inválidos para a consulta.",
      status,
      "validation",
      { ...options, retryable: false },
    );
  }

  if (status === 503) {
    throw new ApiClientError(
      "A fonte de dados está momentaneamente indisponível. Tente novamente em instantes.",
      status,
      "unavailable",
      options,
    );
  }

  const kind: ApiErrorKind = status >= 500 ? "unavailable" : "unknown";
  throw new ApiClientError(
    kind === "unavailable"
      ? "Erro interno ao consultar a API. Tente novamente."
      : parsed.message,
    status,
    kind,
    options,
  );
}

export type HttpRequestOptions = {
  signal?: AbortSignal;
  context?: string;
};

function authHeaders(accept = "application/json"): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: accept,
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
  };
  const token = accessTokenGetter?.();
  if (!token) {
    throw new ApiClientError(
      "É necessário autenticar novamente para continuar.",
      401,
      "auth",
      { retryable: false },
    );
  }
  headers.Authorization = `Bearer ${token}`;
  return headers;
}

export async function httpGet<T>(url: string, options: HttpRequestOptions = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, {
      method: "GET",
      headers: authHeaders(),
      signal: options.signal,
    });
  } catch {
    throw new ApiClientError(
      "Não foi possível conectar à API. Verifique sua conexão e tente novamente.",
      0,
      "unavailable",
      { context: options.context },
    );
  }

  if (!response.ok) {
    let parsed: ParsedApiError = { message: `Erro HTTP ${response.status}` };
    try {
      parsed = formatApiDelpiErrorMessage(await response.json(), parsed.message);
    } catch {
      // mantém mensagem padrão
    }
    classifyHttpError(response.status, parsed, options.context);
  }

  return response.json() as Promise<T>;
}

export async function httpGetBlob(
  url: string,
  options: HttpRequestOptions = {},
): Promise<{ blob: Blob; filename: string; contentType: string }> {
  let response: Response;
  try {
    response = await fetch(url, {
      method: "GET",
      headers: authHeaders("*/*"),
      signal: options.signal,
    });
  } catch {
    throw new ApiClientError(
      "Não foi possível conectar à API. Verifique sua conexão e tente novamente.",
      0,
      "unavailable",
      { context: options.context },
    );
  }

  if (!response.ok) {
    let parsed: ParsedApiError = { message: `Erro HTTP ${response.status}` };
    try {
      parsed = formatApiDelpiErrorMessage(await response.json(), parsed.message);
    } catch {
      // mantém mensagem padrão
    }
    classifyHttpError(response.status, parsed, options.context);
  }

  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = /filename="?([^"]+)"?/i.exec(disposition);
  const filename = match?.[1] || "materiais-terceiros-retornos.csv";
  const contentType = response.headers.get("Content-Type") || "application/octet-stream";
  return { blob: await response.blob(), filename, contentType };
}

export const HTTP_CALLER_APP = DELPI_CALLER_APP;
