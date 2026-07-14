import {
  chartPartAllowsFrame,
  inputPartAllowsFrame,
  isDataBoundEditorBlockType,
  isFetchableDataBlockType,
  kpiPartAllowsFrame,
} from "@delpi/tv-dashboard-presentation";

import { withCommonTail } from "./commonSectionPresets";
import type { SelectionSectionContext, SelectionSectionId } from "./types";

/**
 * Lista ordenada de seções Elemento para ribbon e painel (paridade).
 * Parte selecionada → prioriza seções da parte; bloco sem parte → seções do tipo.
 * O rabo transversal (frame/organize[/animation/actions]) vem de `withCommonTail`.
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
    const head: SelectionSectionId[] = ["partFormat", "typography"];
    if (chartPartAllowsFrame(ctx.selectedChartPart)) {
      return withCommonTail(head, "light");
    }
    return [...head, "organize"];
  }

  if (selected.type === "kpi_view" && ctx.selectedKpiPart) {
    const head: SelectionSectionId[] = ["shapeChrome", "typography"];
    if (kpiPartAllowsFrame(ctx.selectedKpiPart)) {
      return withCommonTail(head, "light");
    }
    return [...head, "organize"];
  }

  if (selected.type === "table_view" && ctx.selectedTablePart) {
    return withCommonTail(["partFormat", "typography"], "light");
  }

  if (selected.type === "input" && ctx.selectedInputPart) {
    const head: SelectionSectionId[] = ["shapeChrome", "inputBinding"];
    if (inputPartAllowsFrame(ctx.selectedInputPart)) {
      return withCommonTail(head, "light");
    }
    return [...head, "organize"];
  }

  switch (selected.type) {
    case "text":
    case "heading":
      return withCommonTail(["typography", "textBox"]);
    case "shape":
      return withCommonTail(["shapeGallery", "shapeChrome", "typography"]);
    case "icon":
      return withCommonTail(["shapeChrome"]);
    case "image":
      return withCommonTail(["media", "imageCrop"]);
    case "video":
      return withCommonTail(["media"]);
    case "canvas_table":
      return withCommonTail(["canvasTable"]);
    case "input":
      return withCommonTail(["shapeChrome", "inputBinding"]);
    case "kpi_view":
      return withCommonTail(["kpiAppearance"]);
    case "chart_view":
      return withCommonTail([
        "typography",
        "chartLayout",
        "chartStyles",
        "chartType",
        "chartLabels",
        "chartAxes",
      ]);
    case "table_view":
      return withCommonTail(["tableStyleOptions", "tableStyles", "tableBorders"]);
    default:
      if (isFetchableDataBlockType(selected.type) || selected.type === "data_source") {
        return withCommonTail(["dataSourceHint"], "light");
      }
      if (isDataBoundEditorBlockType(selected.type)) {
        return withCommonTail([], "light");
      }
      return withCommonTail([]);
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
  "chartLayout",
  "chartStyles",
  "chartType",
  "chartLabels",
  "chartAxes",
  "kpiAppearance",
  "media",
  "imageCrop",
  "canvasTable",
  "partFormat",
  "inputBinding",
  "animation",
  "actions",
]);
