export function formatProductionApiError(reason: unknown): string {
  if (reason instanceof Error) return reason.message;
  if (typeof reason === "string") return reason;
  return "Erro desconhecido";
}
