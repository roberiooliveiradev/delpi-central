type RequestOptions = {
  signal?: AbortSignal;
};

const DELPI_CALLER_APP = "dashboard-hr";

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHttpClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

export async function httpGet<T>(
  url: string,
  options: RequestOptions = {}
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
      message =
        errorBody?.message ||
        errorBody?.detail ||
        errorBody?.error ||
        message;
    } catch {
      // mantém mensagem padrão
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}
