import { FINANCIAL_API_BASE } from "../constants/routes";

type RequestOptions = {
  signal?: AbortSignal;
};

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

const DELPI_CALLER_APP = "financial";
const RETRYABLE_HTTP_STATUSES = new Set([502, 503, 504]);
const HTTP_GET_MAX_ATTEMPTS = 3;

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

export function unwrapEnvelope<T>(response: ApiEnvelope<T>, fallbackMessage: string): T {
  if (response.success === false) {
    throw new Error(response.message?.trim() || fallbackMessage);
  }
  return response.data;
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
  };
  const token = accessTokenGetter?.();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

function formatApiError(errorBody: unknown, status: number): string {
  if (!errorBody || typeof errorBody !== "object") {
    return `Erro HTTP ${status}`;
  }
  const body = errorBody as Record<string, unknown>;
  if (typeof body.message === "string" && body.message.trim()) {
    return body.message;
  }
  return `Erro HTTP ${status}`;
}

export async function httpGet<T>(url: string, options: RequestOptions = {}): Promise<T> {
  let lastMessage = "Erro ao consultar a API.";

  for (let attempt = 1; attempt <= HTTP_GET_MAX_ATTEMPTS; attempt += 1) {
    const response = await fetch(url, {
      method: "GET",
      headers: authHeaders(),
      signal: options.signal,
    });

    if (!response.ok) {
      let message = `Erro HTTP ${response.status}`;
      try {
        message = formatApiError(await response.json(), response.status);
      } catch {
        // mantém o texto padrão quando o corpo não é JSON
      }
      lastMessage = message;

      if (RETRYABLE_HTTP_STATUSES.has(response.status) && attempt < HTTP_GET_MAX_ATTEMPTS) {
        await delay(250 * attempt);
        continue;
      }

      throw new Error(message);
    }

    return response.json() as Promise<T>;
  }

  throw new Error(lastMessage);
}

export function financialApiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${FINANCIAL_API_BASE}${normalized}`;
}
