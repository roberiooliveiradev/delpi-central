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

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { message?: string };
    if (body?.message) return body.message;
  } catch {
    // ignore
  }
  if (response.status === 401) return "Sessão expirada. Faça login novamente.";
  if (response.status === 403) return "Você não tem permissão para esta operação.";
  return `Erro HTTP ${response.status}`;
}

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
    signal: options.signal,
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<T>;
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
  return response.json() as Promise<T>;
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
  return response.json() as Promise<T>;
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
