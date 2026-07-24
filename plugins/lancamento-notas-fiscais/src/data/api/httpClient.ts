type RequestOptions = {
  signal?: AbortSignal;
};

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
  meta?: Record<string, unknown>;
  error?: { code?: string; recoverable?: boolean; meta?: Record<string, unknown> } | null;
};

export class ApiError extends Error {
  status: number;
  code?: string;
  meta?: Record<string, unknown>;

  constructor(
    message: string,
    opts: { status: number; code?: string; meta?: Record<string, unknown> },
  ) {
    super(message);
    this.name = "ApiError";
    this.status = opts.status;
    this.code = opts.code;
    this.meta = opts.meta;
  }
}

const DELPI_CALLER_APP = "lancamento-notas-fiscais";

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

function authHeaders(json = false): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
  };
  if (json) headers["Content-Type"] = "application/json";
  const token = accessTokenGetter?.();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

function friendlyMessage(status: number, fallback: string): string {
  if (status === 401) {
    return "Sessão expirada ou não autenticada. Faça login novamente.";
  }
  if (status === 403) {
    return "Você não tem permissão para realizar esta operação.";
  }
  return fallback;
}

async function parseResponse<T>(response: Response): Promise<T> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }

  if (!response.ok) {
    const record = (body && typeof body === "object" ? body : {}) as Record<
      string,
      unknown
    >;
    const errorObj =
      record.error && typeof record.error === "object"
        ? (record.error as Record<string, unknown>)
        : undefined;
    const code = typeof errorObj?.code === "string" ? errorObj.code : undefined;
    const meta =
      (errorObj?.meta as Record<string, unknown> | undefined) ||
      (record.meta as Record<string, unknown> | undefined);
    const message =
      (typeof record.message === "string" && record.message) ||
      friendlyMessage(response.status, `Erro HTTP ${response.status}`);
    throw new ApiError(message, { status: response.status, code, meta });
  }

  const envelope = body as ApiEnvelope<T>;
  if (envelope && typeof envelope === "object" && "success" in envelope) {
    if (envelope.success === false) {
      throw new ApiError(envelope.message || "Operação não concluída.", {
        status: response.status,
        code: envelope.error?.code,
        meta: envelope.error?.meta,
      });
    }
    return envelope.data;
  }

  return body as T;
}

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
    signal: options.signal,
  });
  return parseResponse<T>(response);
}

export async function httpPost<T>(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: authHeaders(true),
    body: JSON.stringify(body),
    signal: options.signal,
  });
  return parseResponse<T>(response);
}

export async function httpPatch<T>(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "PATCH",
    headers: authHeaders(true),
    body: JSON.stringify(body),
    signal: options.signal,
  });
  return parseResponse<T>(response);
}

export function formatDuplicateMessage(error: ApiError): string {
  const existingId = error.meta?.existing_request_id;
  if (typeof existingId === "string" && existingId) {
    return `${error.message} Solicitação existente: ${existingId}.`;
  }
  return error.message;
}
