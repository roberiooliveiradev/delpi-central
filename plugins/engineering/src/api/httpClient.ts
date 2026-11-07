/** Cliente HTTP do MFE — mesmo padrão dos plugins: Bearer do host via
 * `getAccessToken` prop + caller-app de identificação. O token nunca é
 * persistido, logado ou colocado na URL. */

export const DELPI_CALLER_APP = "engineering";

const REQUEST_TIMEOUT_MS = 15_000;

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

/** Limpeza de sessão — chamada no unmount do MFE. Sem ela, o getter da
 * sessão anterior ficaria acessível para uma remontagem com outro
 * usuário antes do novo configure. */
export function resetHttpClient(): void {
  accessTokenGetter = null;
}

export type HomeApiErrorKind =
  | "unauthorized"
  | "forbidden"
  | "rate_limited"
  | "unavailable"
  | "timeout"
  | "network_error"
  | "contract_error";

export class HomeApiError extends Error {
  readonly kind: HomeApiErrorKind;
  readonly status: number | null;

  constructor(kind: HomeApiErrorKind, message: string, status: number | null = null) {
    super(message);
    this.name = "HomeApiError";
    this.kind = kind;
    this.status = status;
  }
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

function errorForStatus(status: number): HomeApiError {
  if (status === 401) {
    return new HomeApiError(
      "unauthorized",
      "Sua sessão expirou ou não está ativa. Entre novamente pelo Portal.",
      status,
    );
  }
  if (status === 403) {
    return new HomeApiError(
      "forbidden",
      "Você não tem permissão para acessar o Portal Engenharia.",
      status,
    );
  }
  if (status === 429) {
    return new HomeApiError(
      "rate_limited",
      "Muitas chamadas em sequência. Aguarde um instante e tente novamente.",
      status,
    );
  }
  return new HomeApiError(
    "unavailable",
    "A Engineering API está indisponível no momento. Tente novamente em instantes.",
    status,
  );
}

async function getResponse(
  path: string,
  signal?: AbortSignal,
  init?: { method?: string; body?: unknown },
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const onAbort = () => controller.abort();
  signal?.addEventListener("abort", onAbort, { once: true });

  let response: Response;
  try {
    response = await fetch(path, {
      method: init?.method ?? "GET",
      headers:
        init?.body !== undefined
          ? { ...authHeaders(), "Content-Type": "application/json" }
          : authHeaders(),
      credentials: "same-origin",
      body: init?.body !== undefined ? JSON.stringify(init.body) : undefined,
      signal: controller.signal,
    });
  } catch (error) {
    if ((error as Error)?.name === "AbortError") {
      if (signal?.aborted) {
        throw error;
      }
      throw new HomeApiError(
        "timeout",
        "A resposta demorou demais. Tente novamente.",
      );
    }
    throw new HomeApiError(
      "network_error",
      "Falha de comunicação. Verifique sua conexão.",
    );
  } finally {
    clearTimeout(timeout);
    signal?.removeEventListener("abort", onAbort);
  }

  if (!response.ok) {
    throw errorForStatus(response.status);
  }
  return response;
}

export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await getResponse(path, signal);
  return (await response.json()) as T;
}

export async function getBlob(path: string, signal?: AbortSignal): Promise<Blob> {
  const response = await getResponse(path, signal);
  return response.blob();
}

/** Envelope de erro da Engineering API — extrai `message`/`fields` do
 * `fail(...)` oficial para feedback honesto de validação/conflito. */
export type ApiFailBody = {
  success?: boolean;
  message?: string;
  data?: {
    code?: string;
    fields?: Record<string, string>;
  } & Record<string, unknown> | null;
};

export type SendJsonOptions = {
  /** Cabeçalhos extras da chamada (ex.: `Idempotency-Key` em mutações
   * sujeitas a retry — contrato PRC exige o header, não query). */
  headers?: Record<string, string>;
};

async function sendJson<T>(
  method: "POST" | "PUT" | "PATCH" | "DELETE",
  path: string,
  body?: unknown,
  signal?: AbortSignal,
  options?: SendJsonOptions,
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const onAbort = () => controller.abort();
  signal?.addEventListener("abort", onAbort, { once: true });

  let response: Response;
  try {
    response = await fetch(path, {
      method,
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
        ...(options?.headers ?? {}),
      },
      credentials: "same-origin",
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (error) {
    if ((error as Error)?.name === "AbortError") {
      if (signal?.aborted) throw error;
      throw new HomeApiError("timeout", "A resposta demorou demais. Tente novamente.");
    }
    throw new HomeApiError("network_error", "Falha de comunicação. Verifique sua conexão.");
  } finally {
    clearTimeout(timeout);
    signal?.removeEventListener("abort", onAbort);
  }

  if (!response.ok) {
    let failBody: ApiFailBody | null = null;
    try {
      failBody = (await response.json()) as ApiFailBody;
    } catch {
      /* envelope inesperado — cai no erro por status */
    }
    if (
      response.status === 400 ||
      response.status === 409 ||
      response.status === 422
    ) {
      const err = new HomeApiError(
        "contract_error",
        failBody?.message || "Os dados enviados foram recusados.",
        response.status,
      );
      const ext = err as {
        fields?: Record<string, string>;
        code?: string;
        data?: Record<string, unknown> | null;
      };
      ext.fields = failBody?.data?.fields;
      ext.code =
        typeof failBody?.data?.code === "string"
          ? failBody.data.code
          : undefined;
      ext.data = failBody?.data ?? null;
      throw err;
    }
    throw errorForStatus(response.status);
  }
  return (await response.json()) as T;
}

export async function postJson<T>(
  path: string,
  body?: unknown,
  signal?: AbortSignal,
  options?: SendJsonOptions,
): Promise<T> {
  return sendJson<T>("POST", path, body, signal, options);
}

export async function putJson<T>(
  path: string,
  body?: unknown,
  signal?: AbortSignal,
  options?: SendJsonOptions,
): Promise<T> {
  return sendJson<T>("PUT", path, body, signal, options);
}

export async function patchJson<T>(
  path: string,
  body?: unknown,
  signal?: AbortSignal,
  options?: SendJsonOptions,
): Promise<T> {
  return sendJson<T>("PATCH", path, body, signal, options);
}

export async function deleteJson<T>(
  path: string,
  signal?: AbortSignal,
): Promise<T> {
  return sendJson<T>("DELETE", path, undefined, signal);
}
