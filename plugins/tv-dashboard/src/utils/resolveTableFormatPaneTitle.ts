import type { ComunicadoTablePartRef } from "@delpi/tv-dashboard-presentation";

/**
 * Título do painel lateral de tabela conforme a parte selecionada (PPT «Formatar …»).
 */
export function resolveTableFormatPaneTitle(
  selectedTablePart: ComunicadoTablePartRef | null | undefined,
): string {
  if (!selectedTablePart) return "Formatar Tabela";
  switch (selectedTablePart.kind) {
    case "frame":
      return "Formatar Moldura";
    case "title":
      return "Formatar Título da Tabela";
    case "header":
    case "headerCell":
      return "Formatar Cabeçalho";
    case "cell":
      return "Formatar Célula";
    default:
      return "Formatar Tabela";
  }
}
