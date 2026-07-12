import type {
  ComunicadoRibbonTabRequest,
  SelectionPanelTab,
} from "../components/comunicadoEditorContextCore";

/** Pedidos legados (Forma/Gráfico/Tabela/Formatar) → aba Elemento unificada. */
export function normalizeSelectionRibbonTab(
  tab: ComunicadoRibbonTabRequest,
): ComunicadoRibbonTabRequest {
  if (
    tab === "shape" ||
    tab === "chart" ||
    tab === "table" ||
    tab === "format" ||
    tab === "element"
  ) {
    return "element";
  }
  return tab;
}

export function isSelectionPanelTab(tab: string): tab is SelectionPanelTab {
  return tab === "element" || tab === "data" || tab === "layers";
}
