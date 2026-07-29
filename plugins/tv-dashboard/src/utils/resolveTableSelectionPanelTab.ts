import type {
  ComunicadoRibbonTabRequest,
  SelectionPanelTab,
} from "../components/comunicadoEditorContextCore";
import { normalizeSelectionRibbonTab } from "./normalizeSelectionRibbonTab";

/**
 * Aba de formatação canônica do painel lateral para o tipo de bloco.
 * Tabela não tem «Elemento» — só Design / Layout.
 */
export function formatPanelTabForBlockType(
  blockType: string | null | undefined,
  currentPanelTab?: SelectionPanelTab | null,
): SelectionPanelTab {
  if (blockType === "table_view") {
    return currentPanelTab === "tableLayout" ? "tableLayout" : "tableDesign";
  }
  if (blockType === "data_source" || blockType?.startsWith("data_")) {
    return "data";
  }
  return "element";
}

/**
 * Normaliza pedidos de aba (legados `element`/`shape`/`chart`/…) para a aba
 * real do painel, com base no **bloco-alvo** (não na seleção defasada do ref).
 *
 * Sem isso: selecionar gráfico após tabela grava `tableDesign` (inexistente para
 * chart) e o inspetor parece vazio; insert via `selectBlocksByIds` não muda a aba.
 */
export function resolveFormatSelectionPanelTab(options: {
  requested: ComunicadoRibbonTabRequest;
  selectedBlockType: string | null | undefined;
  currentPanelTab?: SelectionPanelTab | null;
}): ComunicadoRibbonTabRequest {
  const normalized = normalizeSelectionRibbonTab(options.requested);
  if (normalized === "data" || normalized === "layers" || normalized === "insert" || normalized === "view") {
    return normalized;
  }
  if (normalized === "tableDesign" || normalized === "tableLayout") {
    if (options.selectedBlockType === "table_view") return normalized;
    return formatPanelTabForBlockType(options.selectedBlockType, options.currentPanelTab);
  }
  if (normalized !== "element") return normalized;
  return formatPanelTabForBlockType(options.selectedBlockType, options.currentPanelTab);
}

/** @deprecated Preferir `resolveFormatSelectionPanelTab`. */
export const resolveTableSelectionPanelTab = resolveFormatSelectionPanelTab;
