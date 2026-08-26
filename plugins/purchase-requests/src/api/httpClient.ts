type RequestOptions = { signal?: AbortSignal };

const DELPI_CALLER_APP = "purchase-requests";

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

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
  }
}

async function parseError(response: Response, bodyText?: string): Promise<string> {
  const text = bodyText ?? (await readBodyText(response));
  if (looksLikeHtml(text, response.headers.get("content-type"))) {
    return "API de solicitações de compra indisponível. Verifique o serviço purchase-requests-api e o gateway.";
  }
  try {
    const body = JSON.parse(text) as { message?: string; detail?: string | unknown };
    if (body?.message) return body.message;
    if (typeof body?.detail === "string" && body.detail.trim()) return body.detail.trim();
    if (Array.isArray(body?.detail) && body.detail.length > 0) {
      const first = body.detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
  } catch {
    // ignore
  }
  if (response.status === 401) return "Sessão expirada. Faça login novamente.";
  if (response.status === 403) {
    return "Você não possui permissão para esta operação (ex.: purchase-requests.admin).";
  }
  if (response.status === 404) return "Solicitação não encontrada ou indisponível.";
  if (response.status === 502 || response.status === 503) {
    return "API de solicitações de compra indisponível. Tente novamente em instantes.";
  }
  return `Erro HTTP ${response.status}`;
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

export async function httpPut<T>(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "PUT",
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

export { DELPI_CALLER_APP };
