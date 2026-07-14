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
  | "shapeChrome"
  | "shapeGallery"
  | "media"
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
  | "tableLayoutDisplay"
  | "tableLayoutAlign"
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
  selectedChartPart?: ComunicadoChartPartRef | null;
  selectedKpiPart?: ComunicadoKpiPartRef | null;
  selectedTablePart?: ComunicadoTablePartRef | null;
  selectedInputPart?: ComunicadoInputPartRef | null;
};
