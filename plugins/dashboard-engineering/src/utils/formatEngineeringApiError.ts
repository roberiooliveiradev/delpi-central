export function formatEngineeringApiError(reason: unknown): string {
  if (reason instanceof Error && reason.message) {
    return reason.message;
  }

  return "Erro ao comunicar com a API de engenharia.";
}
