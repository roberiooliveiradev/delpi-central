export type StatusAprovacaoRevisao = "rascunho" | "em_analise" | "aprovada" | "rejeitada";

export function labelStatusAprovacao(status: string | undefined | null): string {
  switch (status) {
    case "rascunho":
      return "Rascunho";
    case "em_analise":
      return "Em análise";
    case "aprovada":
      return "Aprovada";
    case "rejeitada":
      return "Rejeitada";
    default:
      return status || "—";
  }
}

export function badgeClassStatusAprovacao(status: string | undefined | null): string {
  switch (status) {
    case "aprovada":
      return "ds-badge ds-badge--success";
    case "em_analise":
      return "ds-badge ds-badge--info";
    case "rejeitada":
      return "ds-badge ds-badge--danger";
    default:
      return "ds-badge";
  }
}
