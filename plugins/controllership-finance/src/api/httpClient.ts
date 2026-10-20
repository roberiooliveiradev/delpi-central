import {
  formatApiErrorBody,
  resolveHttpErrorMessage,
} from "./httpErrorMessage";

type RequestOptions = {
  signal?: AbortSignal;
};

/** Única origem de dados do MFE: a BFF do produto. */
export const CONTROLLERSHIP_FINANCE_API_BASE = "/apps/controllership-finance-api";

const DELPI_CALLER_APP = "controllership-finance";

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(
  getAccessToken: () => string | undefined,
) {
  accessTokenGetter = getAccessToken;
}

function buildHeaders(): Record<string, string> {
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

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseError(response: Response): Promise<ApiError> {
  const status = response.status;
  let rawFromBody: string | null = null;
  try {
    const text = await response.text();
    if (text.trim()) {
      try {
        const errorBody: unknown = JSON.parse(text);
        rawFromBody = formatApiErrorBody(errorBody, text);
      } catch {
        rawFromBody = text;
      }
    }
  } catch {
    rawFromBody = null;
  }
  return new ApiError(status, resolveHttpErrorMessage(status, rawFromBody));
}

export function cfApiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${CONTROLLERSHIP_FINANCE_API_BASE}${normalized}`;
}

export async function httpGet<T>(
  url: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: buildHeaders(),
    signal: options.signal,
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  return response.json() as Promise<T>;
}


/** Authenticated image request against this product BFF only. */
export async function httpGetImageBlob(url: string, signal?: AbortSignal): Promise<Blob | null> {
  const response = await fetch(url, { method: "GET", headers: buildHeaders(), signal });
  if (response.status === 404) return null;
  if (!response.ok) throw await parseError(response);
  const mime = (response.headers.get("Content-Type") ?? "").split(";", 1)[0].toLowerCase();
  if (!["image/png", "image/jpeg", "image/webp"].includes(mime)) throw new Error("Invalid image type");
  const blob = await response.blob();
  if (!blob.size || blob.size > 2 * 1024 * 1024) throw new Error("Invalid image size");
  return blob;
}
