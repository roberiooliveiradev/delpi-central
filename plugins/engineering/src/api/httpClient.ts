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

export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const onAbort = () => controller.abort();
  signal?.addEventListener("abort", onAbort, { once: true });

  let response: Response;
  try {
    response = await fetch(path, {
      method: "GET",
      headers: authHeaders(),
      credentials: "same-origin",
      signal: controller.signal,
    });
  } catch (error) {
    if ((error as Error)?.name === "AbortError") {
      if (signal?.aborted) {
        throw error;
      }
      throw new HomeApiError(
        "timeout",
        "A resposta da Engineering API demorou demais. Tente novamente.",
      );
    }
    throw new HomeApiError(
      "network_error",
      "Falha de comunicação com a Engineering API. Verifique sua conexão.",
    );
  } finally {
    clearTimeout(timeout);
    signal?.removeEventListener("abort", onAbort);
  }

  if (!response.ok) {
    throw errorForStatus(response.status);
  }

  return (await response.json()) as T;
}
