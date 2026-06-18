const TRANSIENT_HTTP_STATUSES = new Set([502, 503, 504]);

const DEFAULT_RETRY_DELAYS_MS = [350, 700, 1400, 2800];

export function isTransientHttpStatus(status: number): boolean {
  return TRANSIENT_HTTP_STATUSES.has(status);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

/**
 * fetch com retry para cold start do stack (nginx 502 enquanto a API sobe).
 */
export async function fetchChatApi(
  input: RequestInfo | URL,
  init?: RequestInit,
  retryDelaysMs: number[] = DEFAULT_RETRY_DELAYS_MS,
): Promise<Response> {
  let lastResponse: Response | null = null;

  for (let attempt = 0; attempt <= retryDelaysMs.length; attempt += 1) {
    try {
      const response = await fetch(input, init);
      lastResponse = response;

      if (response.ok || !isTransientHttpStatus(response.status) || attempt >= retryDelaysMs.length) {
        return response;
      }
    } catch (error) {
      if (attempt >= retryDelaysMs.length) {
        throw error;
      }
    }

    await sleep(retryDelaysMs[attempt] ?? retryDelaysMs[retryDelaysMs.length - 1] ?? 500);
  }

  if (lastResponse) {
    return lastResponse;
  }

  throw new Error("Falha ao comunicar com o Minha DELPI Chat.");
}

export function formatTransientChatApiMessage(status: number): string {
  if (isTransientHttpStatus(status)) {
    return "O serviço do chat ainda está iniciando. Aguarde alguns segundos e tente novamente.";
  }

  return `Erro ao comunicar com o Minha DELPI Chat. (HTTP ${status})`;
}

export function isBootstrapLoadErrorMessage(message: string | null | undefined): boolean {
  const normalized = String(message ?? "").trim().toLowerCase();

  if (!normalized) {
    return false;
  }

  return (
    normalized.includes("http 502") ||
    normalized.includes("http 503") ||
    normalized.includes("http 504") ||
    normalized.includes("ainda está iniciando") ||
    normalized.includes("erro ao carregar sessões") ||
    normalized.includes("erro ao carregar agentes") ||
    normalized.includes("erro ao carregar projetos") ||
    normalized.includes("erro ao comunicar com o minha delpi chat")
  );
}
