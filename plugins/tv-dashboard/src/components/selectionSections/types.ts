import type {
  ComunicadoBlock,
  ComunicadoChartPartRef,
  ComunicadoInputPartRef,
  ComunicadoKpiPartRef,
  ComunicadoTablePartRef,
} from "@delpi/tv-dashboard-presentation";

/** Seções canônicas Elemento — mesma lista na ribbon e no painel. */
export type SelectionSectionId =
  | "frame"
  | "display"
  | "organize"
  | "typography"
  | "textBox"
  | "visualBox"
  | "shapeChrome"
  | "iconEditor"
  | "shapeGallery"
  | "media"
  | "appearance"
  | "imageCrop"
  | "canvasTable"
  | "inputBinding"
  | "chartLayout"
  | "chartStyles"
  | "chartType"
  | "chartLabels"
  | "chartAxes"
  | "chartSeries"
  | "tableStyleOptions"
  | "tableBorders"
  | "tableStyles"
  | "tableLayoutData"
  | "tableLayoutAlign"
  | "tableLayoutSize"
  | "kpiAppearance"
  | "animation"
  | "actions"
  | "dataSourceHint"
  | "partFormat"
  | "alignMulti";

export type SelectionSectionLayout = "ribbon" | "pane";

export type SelectionSectionContext = {
  selected: ComunicadoBlock | null;
  selectedIds: string[];
  /** Blocos da seleção (ordem alinhada a selectedIds quando disponível). */
  selectedBlocks?: ComunicadoBlock[];
  selectedChartPart?: ComunicadoChartPartRef | null;
  selectedKpiPart?: ComunicadoKpiPartRef | null;
  selectedTablePart?: ComunicadoTablePartRef | null;
  selectedInputPart?: ComunicadoInputPartRef | null;
};

/**
 * Seções que permanecem single-only mesmo em multi (tamanho absoluto, animação).
 * Organizar já cobre alinhamento/distribuição.
 */
export const MULTI_SELECTION_EXCLUDED_SECTIONS = new Set<SelectionSectionId>([
  "frame",
  "animation",
]);
