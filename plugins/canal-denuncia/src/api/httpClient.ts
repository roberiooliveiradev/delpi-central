type RequestOptions = { signal?: AbortSignal };

const DELPI_CALLER_APP = "canal-denuncia";

type ApiEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
};

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

function authHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
    ...extra,
  };
  const token = accessTokenGetter?.();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

export async function httpPostJson<T>(
  url: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(`HTTP_${response.status}`);
  }

  const payload = (await response.json()) as ApiEnvelope<T> | T;
  if (
    payload &&
    typeof payload === "object" &&
    "success" in payload &&
    "data" in payload
  ) {
    const envelope = payload as ApiEnvelope<T>;
    if (envelope.success === false) {
      throw new Error("REQUEST_FAILED");
    }
    return envelope.data;
  }

  return payload as T;
}
