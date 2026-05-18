export function formatCommercialApiError(reason: unknown): string {
  if (reason instanceof Error) {
    const message = reason.message.trim();
    if (/timeout|timed out|ETIMEDOUT/i.test(message)) {
      return "A consulta ao TOTVS demorou demais. Tente um período menor.";
    }
    if (/403|forbidden|permiss/i.test(message)) {
      return "Sem permissão para acessar os indicadores comerciais.";
    }
    return message;
  }

  return "Erro ao carregar indicadores comerciais.";
}
