type RequestOptions = {
  signal?: AbortSignal;
};

const DELPI_CALLER_APP = "inspecoes-processo";
/** Evita UI presa ~2 min no timeout ODBC padrão da API. */
const CLIENT_REQUEST_TIMEOUT_MS = 45_000;

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

function formatApiDelpiErrorMessage(errorBody: unknown, fallback: string): string {
  if (!errorBody || typeof errorBody !== "object") {
    return fallback;
  }

  const record = errorBody as Record<string, unknown>;
  const base =
    (typeof record.message === "string" && record.message) ||
    (typeof record.detail === "string" && record.detail) ||
    fallback;
  const error = record.error;

  if (error && typeof error === "object") {
    const code = (error as { code?: unknown }).code;
    if (typeof code === "string" && code) {
      return `[${code}] ${base}`;
    }
  }

  return base;
}

function linkAbortSignals(
  external: AbortSignal | undefined,
  local: AbortController,
): () => void {
  if (!external) {
    return () => undefined;
  }
  if (external.aborted) {
    local.abort();
    return () => undefined;
  }
  const onAbort = () => local.abort();
  external.addEventListener("abort", onAbort);
  return () => external.removeEventListener("abort", onAbort);
}

export async function httpGet<T>(
  url: string,
  options: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
  };

  const token = accessTokenGetter?.();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const localController = new AbortController();
  const unlinkExternal = linkAbortSignals(options.signal, localController);
  const timeoutId = window.setTimeout(() => {
    localController.abort();
  }, CLIENT_REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      method: "GET",
      headers,
      signal: localController.signal,
    });

    if (!response.ok) {
      let message = `Erro HTTP ${response.status}`;
      if (response.status === 504 || response.status === 502) {
        message =
          "A consulta demorou demais (timeout). Refine os filtros (produto, OP ou período) e tente novamente.";
      }
      try {
        const errorBody = await response.json();
        message = formatApiDelpiErrorMessage(errorBody, message);
      } catch {
        // mantém mensagem padrão / timeout
      }
      throw new Error(message);
    }

    return response.json() as Promise<T>;
  } catch (err) {
    if (
      err instanceof DOMException &&
      err.name === "AbortError" &&
      !options.signal?.aborted
    ) {
      throw new Error(
        "A consulta demorou demais. Refine os filtros (produto ou OP) e tente novamente.",
      );
    }
    throw err;
  } finally {
    window.clearTimeout(timeoutId);
    unlinkExternal();
  }
}
