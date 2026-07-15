type RequestOptions = {
  signal?: AbortSignal;
};

const DELPI_CALLER_APP = "guias-procedimentos";

let accessTokenGetter: (() => string | undefined) | null = null;

export class HttpRequestError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "HttpRequestError";
    this.status = status;
  }
}

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
      return `${base}`;
    }
  }

  return base;
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

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      message = formatApiDelpiErrorMessage(errorBody, message);
    } catch {
      // mantém mensagem padrão
    }
    throw new HttpRequestError(message, response.status);
  }

  return response.json() as Promise<T>;
}

export async function httpGet<T>(
  url: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
    signal: options.signal,
  });
  return parseJson<T>(response);
}

export async function httpPost<T>(
  url: string,
  body?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      ...authHeaders(),
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal: options.signal,
  });
  return parseJson<T>(response);
}

export async function httpPut<T>(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "PUT",
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    signal: options.signal,
  });
  return parseJson<T>(response);
}

/** Multipart: não definir Content-Type (boundary gerado pelo browser). */
export async function httpPostForm<T>(
  url: string,
  formData: FormData,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
    signal: options.signal,
  });
  return parseJson<T>(response);
}

export type UploadProgressCallback = (ratio: number) => void;

/**
 * Upload multipart com progresso (XHR).
 * `ratio` ∈ [0, 1]; se o browser não reportar, fica em 0 até concluir.
 */
export function httpPostFormWithProgress<T>(
  url: string,
  formData: FormData,
  options: RequestOptions & { onProgress?: UploadProgressCallback } = {},
): Promise<T> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url);
    const headers = authHeaders();
    Object.entries(headers).forEach(([key, value]) => {
      xhr.setRequestHeader(key, value);
    });
    xhr.responseType = "json";

    if (options.signal) {
      if (options.signal.aborted) {
        reject(new DOMException("Aborted", "AbortError"));
        return;
      }
      options.signal.addEventListener(
        "abort",
        () => {
          xhr.abort();
          reject(new DOMException("Aborted", "AbortError"));
        },
        { once: true },
      );
    }

    xhr.upload.onprogress = (event) => {
      if (!options.onProgress) return;
      if (event.lengthComputable && event.total > 0) {
        options.onProgress(event.loaded / event.total);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve((xhr.response ?? {}) as T);
        return;
      }
      const body = xhr.response;
      const message = formatApiDelpiErrorMessage(
        body,
        `Erro HTTP ${xhr.status}`,
      );
      reject(new HttpRequestError(message, xhr.status));
    };

    xhr.onerror = () => {
      reject(new HttpRequestError("Falha de rede no upload.", 0));
    };

    xhr.send(formData);
  });
}

export async function httpGetBlob(
  url: string,
  options: RequestOptions = {},
): Promise<Blob> {
  const response = await fetch(url, {
    method: "GET",
    headers: authHeaders(),
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
    throw new HttpRequestError(message, response.status);
  }
  return response.blob();
}
