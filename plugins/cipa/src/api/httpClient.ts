type RequestOptions = { signal?: AbortSignal };

const DELPI_CALLER_APP = "cipa";

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
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

async function parseError(response: Response, bodyText?: string): Promise<string> {
  const text = bodyText ?? (await readBodyText(response));
  if (looksLikeHtml(text, response.headers.get("content-type"))) {
    return "API CIPA indisponível (resposta HTML no lugar de JSON). Verifique se o serviço cipa-api e o gateway estão no ar.";
  }
  try {
    const body = JSON.parse(text) as { message?: string };
    if (body?.message) return body.message;
  } catch {
    // ignore
  }
  if (response.status === 401) return "Sessão expirada. Faça login novamente.";
  if (response.status === 403) return "Você não tem permissão para esta operação.";
  if (response.status === 502 || response.status === 503) {
    return "API CIPA indisponível. Tente novamente em instantes.";
  }
  return `Erro HTTP ${response.status}`;
}

async function parseJson<T>(response: Response): Promise<T> {
  const text = await readBodyText(response);
  if (looksLikeHtml(text, response.headers.get("content-type"))) {
    throw new Error(await parseError(response, text));
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error(
      "Resposta inválida da API CIPA (não é JSON). Verifique o serviço cipa-api e o gateway.",
    );
  }
}

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
    signal: options.signal,
  });
  if (!response.ok) throw new Error(await parseError(response));
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
  if (!response.ok) throw new Error(await parseError(response));
  return parseJson<T>(response);
}

export async function httpForm<T>(
  url: string,
  form: FormData,
  options: RequestOptions & { idempotencyKey?: string } = {},
): Promise<T> {
  const headers = authHeaders();
  if (options.idempotencyKey) headers["Idempotency-Key"] = options.idempotencyKey;
  const response = await fetch(url, {
    method: "POST",
    headers,
    body: form,
    signal: options.signal,
  });
  if (!response.ok) throw new Error(await parseError(response));
  return parseJson<T>(response);
}

export async function httpBlob(url: string, options: RequestOptions = {}): Promise<Blob> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
    signal: options.signal,
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.blob();
}
