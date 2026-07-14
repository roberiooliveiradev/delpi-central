import {
  chartPartAllowsFrame,
  inputPartAllowsFrame,
  isDataBoundEditorBlockType,
  isFetchableDataBlockType,
  kpiPartAllowsFrame,
} from "@delpi/tv-dashboard-presentation";

import type { SelectionSectionContext, SelectionSectionId } from "./types";

/**
 * Lista ordenada de seções Elemento para ribbon e painel (paridade).
 * Parte selecionada → prioriza seções da parte; bloco sem parte → seções do tipo.
 */
export function resolveSelectionSections(
  ctx: SelectionSectionContext,
): SelectionSectionId[] {
  const { selected, selectedIds } = ctx;
  if (!selected || selectedIds.length === 0) return [];

  if (selectedIds.length >= 2) {
    return ["alignMulti", "organize"];
  }

  if (selected.type === "chart_view" && ctx.selectedChartPart) {
    const sections: SelectionSectionId[] = ["partFormat"];
    if (chartPartAllowsFrame(ctx.selectedChartPart)) {
      sections.push("frame");
    }
    sections.push("organize");
    return sections;
  }

  if (selected.type === "kpi_view" && ctx.selectedKpiPart) {
    const sections: SelectionSectionId[] = ["shapeChrome", "typography"];
    if (kpiPartAllowsFrame(ctx.selectedKpiPart)) {
      sections.push("frame");
    }
    sections.push("organize");
    return sections;
  }

  if (selected.type === "table_view" && ctx.selectedTablePart) {
    return ["partFormat", "frame", "organize"];
  }

  if (selected.type === "input" && ctx.selectedInputPart) {
    const sections: SelectionSectionId[] = ["shapeChrome", "inputBinding"];
    if (inputPartAllowsFrame(ctx.selectedInputPart)) {
      sections.push("frame");
    }
    sections.push("organize");
    return sections;
  }

  switch (selected.type) {
    case "text":
    case "heading":
      return [
        "typography",
        "textBox",
        "frame",
        "organize",
        "animation",
        "actions",
      ];
    case "shape":
      return [
        "shapeGallery",
        "shapeChrome",
        "typography",
        "frame",
        "organize",
        "animation",
        "actions",
      ];
    case "icon":
      return ["shapeChrome", "frame", "organize", "animation", "actions"];
    case "image":
      return ["media", "imageCrop", "frame", "organize", "animation", "actions"];
    case "video":
      return ["media", "frame", "organize", "animation", "actions"];
    case "canvas_table":
      return ["canvasTable", "frame", "organize", "animation", "actions"];
    case "input":
      return [
        "shapeChrome",
        "inputBinding",
        "frame",
        "organize",
        "animation",
        "actions",
      ];
    case "kpi_view":
      return ["kpiAppearance", "frame", "organize", "animation", "actions"];
    case "chart_view":
      return [
        "chartLayout",
        "chartStyles",
        "chartType",
        "chartLabels",
        "chartAxes",
        "frame",
        "organize",
        "animation",
        "actions",
      ];
    case "table_view":
      return [
        "tableStyleOptions",
        "tableStyles",
        "tableBorders",
        "frame",
        "organize",
        "animation",
        "actions",
      ];
    default:
      if (isFetchableDataBlockType(selected.type) || selected.type === "data_source") {
        return ["dataSourceHint", "frame", "organize"];
      }
      if (isDataBoundEditorBlockType(selected.type)) {
        return ["frame", "organize"];
      }
      return ["frame", "organize", "animation", "actions"];
  }
}

/** Seções já migradas para host compartilhado (ribbon + pane). */
export const SHARED_HOST_SECTIONS = new Set<SelectionSectionId>([
  "frame",
  "organize",
  "alignMulti",
  "dataSourceHint",
  "typography",
  "textBox",
  "shapeGallery",
  "shapeChrome",
  "tableStyleOptions",
  "tableStyles",
  "tableBorders",
  "animation",
  "actions",
]);
