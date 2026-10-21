export const CALLER_APP = "metalography";

export class HttpRequestError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "HttpRequestError";
    this.status = status;
    this.code = code;
  }
}

export type JsonResult<T> = {
  data: T;
  etag: string | null;
  operationId: string | null;
};

type Envelope<T> = {
  success?: boolean;
  message?: string;
  data?: T;
  meta?: { operationId?: string };
  error?: { code?: string } | null;
  detail?: unknown;
};

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

export function formatApiError(body: unknown, status: number): { message: string; code?: string } {
  if (status === 401) return { message: "Sessão expirada. Entre novamente para continuar." };
  if (status === 403) return { message: "Você não tem permissão para esta ação." };
  if (!body || typeof body !== "object") return { message: `Erro HTTP ${status}` };
  const record = body as Envelope<unknown>;
  const code = record.error?.code;
  if (typeof record.message === "string" && record.message.trim()) {
    return { message: record.message.trim(), code };
  }
  if (typeof record.detail === "string" && record.detail.trim()) {
    return { message: record.detail.trim(), code };
  }
  if (status === 412) {
    return { message: "O relatório foi alterado por outra pessoa. Recarregue antes de gravar.", code };
  }
  if (status === 428) {
    return { message: "A versão do relatório não foi enviada. Recarregue e tente de novo.", code };
  }
  return { message: `Erro HTTP ${status}`, code };
}

function headers(extra?: HeadersInit): Headers {
  const result = new Headers(extra);
  result.set("X-Delpi-Caller-App", CALLER_APP);
  const token = accessTokenGetter?.();
  if (token) result.set("Authorization", `Bearer ${token}`);
  return result;
}

async function readBody(response: Response): Promise<unknown> {
  const type = response.headers.get("content-type") ?? "";
  if (type.includes("application/json")) return response.json();
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return { message: text };
  }
}

export async function requestJson<T>(
  path: string,
  init: RequestInit & { ifMatch?: string | null; idempotencyKey?: string | null } = {},
): Promise<JsonResult<T>> {
  const requestHeaders = headers(init.headers);
  if (init.body && !(init.body instanceof FormData) && !requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }
  if (init.ifMatch) requestHeaders.set("If-Match", init.ifMatch);
  if (init.idempotencyKey) requestHeaders.set("Idempotency-Key", init.idempotencyKey);
  const response = await fetch(path, { ...init, headers: requestHeaders });
  if (response.status === 401 || response.status === 403 || !response.ok) {
    const body = await readBody(response);
    const formatted = formatApiError(body, response.status);
    throw new HttpRequestError(formatted.message, response.status, formatted.code);
  }
  const body = (await readBody(response)) as Envelope<T>;
  if (body?.success === false) {
    const formatted = formatApiError(body, response.status);
    throw new HttpRequestError(formatted.message, response.status, formatted.code);
  }
  return {
    data: body.data as T,
    etag: response.headers.get("ETag"),
    operationId: body.meta?.operationId ?? null,
  };
}

export async function requestBlob(path: string): Promise<{ blob: Blob; contentType: string }> {
  const response = await fetch(path, { headers: headers() });
  if (!response.ok) {
    const body = await readBody(response);
    const formatted = formatApiError(body, response.status);
    throw new HttpRequestError(formatted.message, response.status, formatted.code);
  }
  return {
    blob: await response.blob(),
    contentType: response.headers.get("content-type") ?? "application/octet-stream",
  };
}
