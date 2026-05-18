const TOTVS_HINT =
  "Reduza o intervalo de datas ou remova filtros opcionais e tente novamente.";

function includesAny(text: string, needles: string[]): boolean {
  const lower = text.toLowerCase();
  return needles.some((needle) => lower.includes(needle));
}

/**
 * Converte erros HTTP/rede/TOTVS em mensagens acionáveis para o usuário.
 */
export function formatQualityApiError(error: unknown): string {
  if (error instanceof DOMException && error.name === "AbortError") {
    return "";
  }

  const raw =
    error instanceof Error
      ? error.message
      : typeof error === "string"
        ? error
        : "Erro ao carregar dados de qualidade";

  if (!raw.trim()) {
    return "Erro ao carregar dados de qualidade";
  }

  if (includesAny(raw, ["failed to fetch", "networkerror", "load failed"])) {
    return `Não foi possível conectar à API de qualidade. Verifique sua rede e tente novamente.`;
  }

  if (
    includesAny(raw, [
      "timeout",
      "timed out",
      "etimedout",
      "gateway timeout",
      "504",
    ])
  ) {
    return `A consulta ao TOTVS demorou demais. ${TOTVS_HINT}`;
  }

  if (includesAny(raw, ["502", "bad gateway", "503", "service unavailable"])) {
    return `O serviço de qualidade está indisponível no momento. Aguarde alguns minutos e tente novamente.`;
  }

  if (
    includesAny(raw, [
      "totvs",
      "protheus",
      "sql",
      "odbc",
      "connection refused",
      "erp",
    ])
  ) {
    return `Falha ao consultar o TOTVS: ${raw}. ${TOTVS_HINT}`;
  }

  if (includesAny(raw, ["401", "403", "unauthorized", "forbidden"])) {
    return `Sem permissão para acessar os dados de qualidade. Verifique seu login ou perfil.`;
  }

  return raw;
}
