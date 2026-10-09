import { getTransformometroClientId } from "../../utils/clientId";

export const TRANSFORMOMETRO_API_BASE =
  import.meta.env.VITE_TRANSFORMOMETRO_API_BASE?.trim() ||
  "/apps/transformometro-api/transformometro";

/** Header lido pela API para actorClientId no evento WS (anti-eco por aba). */
export const TRANSFORMOMETRO_CLIENT_ID_HEADER = "X-Transformometro-Client-Id";

/**
 * Budget governado de chamadas HTTP do MFE (G9-LOAD-1 §5 /
 * http-integration-resilience): nenhuma chamada permanece pendente
 * indefinidamente — timeout aborta o fetch e classifica como
 * TmRequestTimeoutError (transitório, recuperável com retry do usuário).
 * Cobre headers + leitura do body (o caller passa o parse para dentro).
 */
export const TM_REQUEST_TIMEOUT_MS = 20_000;

export class TmRequestTimeoutError extends Error {
  readonly path: string;
  constructor(path: string) {
    super("A requisição ao Transformômetro excedeu o tempo limite.");
    this.name = "TmRequestTimeoutError";
    this.path = path;
  }
}

/** Abort externo do consumidor — não é timeout, repassar o erro original. */
export function isExternalAbort(signal: AbortSignal | null | undefined): boolean {
  return !!signal?.aborted;
}

export async function tmRequest<T>(
  path: string,
  init: RequestInit | undefined,
  read: (response: Response) => Promise<T>,
): Promise<T> {
  const external = init?.signal;
  const controller = new AbortController();
  const onExternalAbort = () => controller.abort();
  external?.addEventListener("abort", onExternalAbort, { once: true });
  const timer = setTimeout(() => controller.abort(), TM_REQUEST_TIMEOUT_MS);
  const timedOut = () => controller.signal.aborted && !isExternalAbort(external);
  try {
    const response = await fetch(`${TRANSFORMOMETRO_API_BASE}${path}`, {
      ...init,
      signal: controller.signal,
    });
    return await read(response);
  } catch (err) {
    if (timedOut()) throw new TmRequestTimeoutError(path);
    throw err;
  } finally {
    clearTimeout(timer);
    external?.removeEventListener("abort", onExternalAbort);
  }
}

export function buildAuthHeaders(getAccessToken?: () => string | undefined): HeadersInit {
  const headers: Record<string, string> = {
    [TRANSFORMOMETRO_CLIENT_ID_HEADER]: getTransformometroClientId(),
  };
  const token = getAccessToken?.();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}
