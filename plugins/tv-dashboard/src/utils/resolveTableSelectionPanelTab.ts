import type {
  ComunicadoRibbonTabRequest,
  SelectionPanelTab,
} from "../components/comunicadoEditorContextCore";
import { normalizeSelectionRibbonTab } from "./normalizeSelectionRibbonTab";

/**
 * Tabela não tem aba «Elemento» no painel — só Design da Tabela / Layout.
 * Pedidos legados `element` (ex.: selectTablePart) devem mapear para Design/Layout,
 * senão `panelFocus=element` esconde as seções e a sidebar parece vazia.
 */
export function resolveTableSelectionPanelTab(options: {
  requested: ComunicadoRibbonTabRequest;
  selectedBlockType: string | null | undefined;
  /** Usado quando o pedido é `element` e já estamos em Layout. */
  currentPanelTab?: SelectionPanelTab | null;
}): ComunicadoRibbonTabRequest {
  const normalized = normalizeSelectionRibbonTab(options.requested);
  if (normalized !== "element") return normalized;
  if (options.selectedBlockType !== "table_view") return "element";
  return options.currentPanelTab === "tableLayout" ? "tableLayout" : "tableDesign";
}
