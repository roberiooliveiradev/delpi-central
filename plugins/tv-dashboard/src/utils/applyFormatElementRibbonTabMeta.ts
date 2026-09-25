import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import type { DeckRibbonTabMeta, SelectionPanelTabMeta } from "../components/deck/deckRibbonTabMeta";

/**
 * Labels contextuais «Formatar …» para a aba Elemento (RIBBON-TEXT-001).
 * Não cria aba Início permanente — só renomeia o contextual existente.
 */
export function resolveFormatElementTabLabel(
  selected: ComunicadoBlock | null | undefined,
): string {
  if (!selected) return "Elemento";
  switch (selected.type) {
    case "text":
    case "heading":
      return "Formatar Texto";
    case "shape":
      return "Formatar Forma";
    case "chart_view":
      return "Formatar Gráfico";
    case "kpi_view":
      return "Formatar KPI";
    case "image":
      return "Formatar Imagem";
    case "video":
      return "Formatar Vídeo";
    case "icon":
      return "Formatar Ícone";
    case "input":
      return "Formatar Filtro";
    case "canvas_table":
      return "Formatar Grade";
    default:
      return "Elemento";
  }
}

export function applyFormatElementRibbonTabMeta<
  T extends DeckRibbonTabMeta | SelectionPanelTabMeta,
>(tabs: readonly T[], selected: ComunicadoBlock | null | undefined): T[] {
  const label = resolveFormatElementTabLabel(selected);
  if (label === "Elemento") return [...tabs];
  return tabs.map((tab) =>
    tab.id === "element"
      ? {
          ...tab,
          label,
        }
      : tab,
  );
}
