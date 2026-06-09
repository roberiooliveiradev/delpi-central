import { getAuthToken } from "../lib/auth";

const API_BASE = "/apps/api-delpi";
const DELPI_CALLER_APP = "api-delpi-console";

export type ApiFetchResult<T = unknown> = {
  ok: boolean;
  status: number;
  durationMs: number;
  data: T | null;
  rawText: string;
  headers: Record<string, string>;
  url: string;
  method: string;
};

function buildHeaders(extra?: Record<string, string>): HeadersInit {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
    ...extra,
  };
  const token = getAuthToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

export async function apiFetch<T = unknown>(
  path: string,
  options: {
    method?: string;
    query?: Record<string, string | number | boolean | undefined>;
    body?: unknown;
    headers?: Record<string, string>;
  } = {},
): Promise<ApiFetchResult<T>> {
  const method = (options.method ?? "GET").toUpperCase();
  const url = new URL(`${API_BASE}${path}`, window.location.origin);

  if (options.query) {
    for (const [key, value] of Object.entries(options.query)) {
      if (value === undefined || value === "") continue;
      url.searchParams.set(key, String(value));
    }
  }

  const headers = buildHeaders(options.headers);
  const init: RequestInit = { method, headers };

  if (options.body !== undefined && method !== "GET" && method !== "HEAD") {
    if (typeof options.body === "string") {
      init.body = options.body;
    } else {
      (headers as Record<string, string>)["Content-Type"] = "application/json";
      init.body = JSON.stringify(options.body);
    }
  }

  const started = performance.now();
  const response = await fetch(url.toString(), init);
  const durationMs = Math.round(performance.now() - started);
  const rawText = await response.text();

  const responseHeaders: Record<string, string> = {};
  response.headers.forEach((value, key) => {
    responseHeaders[key] = value;
  });

  let data: T | null = null;
  if (rawText) {
    try {
      data = JSON.parse(rawText) as T;
    } catch {
      data = null;
    }
  }

  return {
    ok: response.ok,
    status: response.status,
    durationMs,
    data,
    rawText,
    headers: responseHeaders,
    url: url.toString(),
    method,
  };
}

export async function fetchOpenApiSpec(): Promise<unknown> {
  const result = await apiFetch("/openapi.json");
  if (!result.ok || !result.data) {
    throw new Error(`Falha ao carregar OpenAPI (${result.status})`);
  }
  return result.data;
}

export async function fetchHealth(): Promise<ApiFetchResult> {
  return apiFetch("/health");
}
