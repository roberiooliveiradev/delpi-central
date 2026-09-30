type RequestOptions = { signal?: AbortSignal; body?: unknown };

type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

export const DELPI_MES_API_BASE = "/apps/delpi-mes-api";
const CALLER_APP = "delpi-mes";
let accessTokenGetter: (() => string | undefined) | null = null;

export class DelpiMesRequestError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "DelpiMesRequestError";
    this.status = status;
  }
}

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

async function httpRequest<T>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": CALLER_APP,
  };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  const token = accessTokenGetter?.();
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${DELPI_MES_API_BASE}${path}`, {
    method,
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  });
  const body = await parseEnvelope<T>(response);
  if (!response.ok || !body.success) {
    throw new DelpiMesRequestError(
      body.message || friendlyStatusMessage(response.status),
      response.status,
    );
  }
  return body.data;
}

export function httpGet<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return httpRequest<T>("GET", path, options);
}

export function httpPost<T>(path: string, body: unknown, options: RequestOptions = {}): Promise<T> {
  return httpRequest<T>("POST", path, { ...options, body });
}

export function httpPut<T>(path: string, body: unknown, options: RequestOptions = {}): Promise<T> {
  return httpRequest<T>("PUT", path, { ...options, body });
}

export function httpPatch<T>(path: string, body: unknown, options: RequestOptions = {}): Promise<T> {
  return httpRequest<T>("PATCH", path, { ...options, body });
}

async function parseEnvelope<T>(response: Response): Promise<ApiEnvelope<T>> {
  try {
    const body = (await response.json()) as Partial<ApiEnvelope<T>>;
    if (typeof body.success !== "boolean" || typeof body.message !== "string" || !("data" in body)) {
      throw new Error("invalid envelope");
    }
    return body as ApiEnvelope<T>;
  } catch {
    throw new DelpiMesRequestError("O Delpi MES recebeu uma resposta inválida.", response.status);
  }
}

function friendlyStatusMessage(status: number): string {
  if (status === 401) return "Sua sessão expirou. Entre novamente na Minha DELPI.";
  if (status === 403) return "Você não possui permissão para acessar esta área.";
  if (status === 502 || status === 503) return "Os dados MES estão temporariamente indisponíveis.";
  return "Não foi possível concluir a consulta ao Delpi MES.";
}
