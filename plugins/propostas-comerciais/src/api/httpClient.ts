type RequestOptions = {
  signal?: AbortSignal;
};

const DELPI_CALLER_APP = "propostas-comerciais";

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

  const response = await fetch(url, {
    method: "GET",
    headers,
    signal: options.signal,
  });

  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      message = formatApiDelpiErrorMessage(errorBody, message);
    } catch {
      // mantém mensagem padrão
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function httpGetBlob(
  url: string,
  options: RequestOptions = {},
): Promise<{ blob: Blob; filename: string | null; contentType: string | null }> {
  const headers: Record<string, string> = {
    Accept: "application/pdf",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
  };

  const token = accessTokenGetter?.();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method: "GET",
    headers,
    signal: options.signal,
  });

  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      message = formatApiDelpiErrorMessage(errorBody, message);
    } catch {
      // resposta pode ser binária/texto
    }
    throw new Error(message);
  }

  const contentDisposition = response.headers.get("Content-Disposition");
  const filenameMatch = contentDisposition?.match(/filename=\"?([^\";]+)\"?/i);
  const filename = filenameMatch?.[1]?.trim() ?? null;

  return {
    blob: await response.blob(),
    filename,
    contentType: response.headers.get("Content-Type"),
  };
}

async function requestPdfBlob(
  url: string,
  method: "GET" | "POST",
  options: RequestOptions & { body?: unknown } = {},
): Promise<{ blob: Blob; filename: string | null; contentType: string | null }> {
  const headers: Record<string, string> = {
    Accept: "application/pdf",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
  };

  if (method === "POST") {
    headers["Content-Type"] = "application/json";
  }

  const token = accessTokenGetter?.();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method,
    headers,
    body: method === "POST" ? JSON.stringify(options.body ?? {}) : undefined,
    signal: options.signal,
  });

  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      message = formatApiDelpiErrorMessage(errorBody, message);
    } catch {
      // resposta pode ser binária/texto
    }
    throw new Error(message);
  }

  const contentDisposition = response.headers.get("Content-Disposition");
  const filenameMatch = contentDisposition?.match(/filename=\"?([^\";]+)\"?/i);
  const filename = filenameMatch?.[1]?.trim() ?? null;

  return {
    blob: await response.blob(),
    filename,
    contentType: response.headers.get("Content-Type"),
  };
}

export async function httpPostBlob(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<{ blob: Blob; filename: string | null; contentType: string | null }> {
  return requestPdfBlob(url, "POST", { ...options, body });
}
