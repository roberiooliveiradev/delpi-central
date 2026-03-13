type RequestOptions = {
  token?: string;
  signal?: AbortSignal;
};

export async function httpGet<T>(
  url: string,
  options: RequestOptions = {}
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json"
  };

  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }

  const response = await fetch(url, {
    method: "GET",
    headers,
    signal: options.signal
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