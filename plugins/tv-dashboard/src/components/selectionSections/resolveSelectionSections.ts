/**
 * Lista ordenada de seções Elemento para ribbon e painel (paridade).
 * Parte selecionada → prioriza seções da parte; bloco sem parte → seções do tipo.
 * Multi-seleção → interseção das seções single de cada bloco (padrão Figma).
 * O rabo transversal (display/organize[/animation/actions]) vem de `withCommonTail`.
 */

import {
  chartPartAllowsFrame,
  inputPartAllowsFrame,
  isDataBoundEditorBlockType,
  isFetchableDataBlockType,
  kpiPartAllowsFrame,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import { withCommonTail } from "./commonSectionPresets";
import {
  MULTI_SELECTION_EXCLUDED_SECTIONS,
  type SelectionSectionContext,
  type SelectionSectionId,
} from "./types";
import {
  filterMultiExcludedSections,
  intersectOrderedIds,
} from "../../utils/selectionSectionIntersect";

function resolveSingleBlockSections(
  selected: ComunicadoBlock,
  ctx: SelectionSectionContext,
): SelectionSectionId[] {
  if (selected.type === "chart_view" && ctx.selectedChartPart) {
    const part = ctx.selectedChartPart;
    const seriesColorPart =
      part.kind === "series" || part.kind === "legend" || part.kind === "marker";
    const head: SelectionSectionId[] = ["partFormat", "typography"];
    if (seriesColorPart) {
      head.push("chartSeries", "chartLayout", "chartStyles", "chartType", "chartLabels", "chartAxes");
      return withCommonTail(head, "light");
    }
    if (chartPartAllowsFrame(part)) {
      return withCommonTail(head, "light");
    }
    return [...head, "appearance", "organize", "actions"];
  }

  if (selected.type === "kpi_view" && ctx.selectedKpiPart) {
    if (ctx.selectedKpiPart.kind === "metricCard") {
      return withCommonTail(["kpiAppearance"]);
    }
    const head: SelectionSectionId[] = ["shapeChrome", "typography"];
    if (kpiPartAllowsFrame(ctx.selectedKpiPart)) {
      return withCommonTail(head, "light");
    }
    return [...head, "appearance", "organize", "actions"];
  }

  if (selected.type === "table_view" && ctx.selectedTablePart) {
    return withCommonTail(["partFormat", "typography"], "light");
  }

  if (selected.type === "input" && ctx.selectedInputPart) {
    const head: SelectionSectionId[] = ["shapeChrome", "inputBinding"];
    if (inputPartAllowsFrame(ctx.selectedInputPart)) {
      return withCommonTail(head, "light");
    }
    return [...head, "appearance", "organize", "actions"];
  }

  switch (selected.type) {
    case "text":
    case "heading":
    case "shape":
      return withCommonTail(["visualBox"]);
    case "icon":
      return withCommonTail(["iconEditor"]);
    case "image":
      return withCommonTail(["media", "imageCrop", "appearance"]);
    case "video":
      return withCommonTail(["media", "appearance"]);
    case "canvas_table":
      return withCommonTail(["canvasTable"]);
    case "input":
      return withCommonTail(["shapeChrome", "inputBinding"]);
    case "kpi_view":
      return withCommonTail(["kpiAppearance", "appearance"]);
    case "chart_view":
      return withCommonTail([
        "typography",
        "chartLayout",
        "chartStyles",
        "chartType",
        "chartLabels",
        "chartAxes",
        "chartSeries",
        "appearance",
      ]);
    case "table_view":
      return withCommonTail([
        "tableStyleOptions",
        "tableStyles",
        "tableTypography",
        "tableBorders",
        "tableLayoutData",
        "tableLayoutSize",
        "tableLayoutAlign",
      ]);
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

function resolveBlocksForMulti(ctx: SelectionSectionContext, ids: string[]): ComunicadoBlock[] {
  const fromCtx = ctx.selectedBlocks?.filter((block) => ids.includes(block.id)) ?? [];
  if (fromCtx.length === ids.length) {
    return ids
      .map((id) => fromCtx.find((block) => block.id === id))
      .filter((block): block is ComunicadoBlock => Boolean(block));
  }
  if (ctx.selected && ids.includes(ctx.selected.id) && fromCtx.length === 0) {
    return [ctx.selected];
  }
  return fromCtx.length > 0 ? fromCtx : ctx.selected ? [ctx.selected] : [];
}

/**
 * Lista ordenada de seções Elemento para ribbon e painel (paridade).
 */
export function resolveSelectionSections(
  ctx: SelectionSectionContext,
): SelectionSectionId[] {
  const { selected, selectedIds } = ctx;
  if (!selected) return [];
  const ids =
    selectedIds && selectedIds.length > 0 ? selectedIds : [selected.id];

  if (ids.length >= 2) {
    const blocks = resolveBlocksForMulti(ctx, ids);
    if (blocks.length < 2) {
      return filterMultiExcludedSections(
        ["organize", "actions"],
        MULTI_SELECTION_EXCLUDED_SECTIONS,
      );
    }
    const perBlock = blocks.map((block) =>
      resolveSingleBlockSections(block, {
        ...ctx,
        selected: block,
        selectedIds: [block.id],
        selectedBlocks: [block],
        /* Multi de blocos soltos: partes KPI/chart/table não aplicam à interseção. */
        selectedChartPart: null,
        selectedKpiPart: null,
        selectedTablePart: null,
        selectedInputPart: null,
      }),
    );
    const intersected = intersectOrderedIds(perBlock);
    const withOrganizeActions = intersected.includes("organize")
      ? intersected
      : [...intersected.filter((id) => id !== "actions"), "organize", "actions"];
    return filterMultiExcludedSections(
      withOrganizeActions.includes("actions")
        ? withOrganizeActions
        : [...withOrganizeActions, "actions"],
      MULTI_SELECTION_EXCLUDED_SECTIONS,
    );
  }

  return resolveSingleBlockSections(selected, ctx);
}

/** Seções já migradas para host compartilhado (ribbon + pane). */
export const SHARED_HOST_SECTIONS = new Set<SelectionSectionId>([
  "frame",
  "display",
  "organize",
  "alignMulti",
  "dataSourceHint",
  "typography",
  "textBox",
  "visualBox",
  "shapeGallery",
  "shapeChrome",
  "iconEditor",
  "tableStyleOptions",
  "tableStyles",
  "tableTypography",
  "tableBorders",
  "tableLayoutData",
  "tableLayoutSize",
  "tableLayoutAlign",
  "chartLayout",
  "chartStyles",
  "chartType",
  "chartLabels",
  "chartAxes",
  "chartSeries",
  "kpiAppearance",
  "media",
  "appearance",
  "imageCrop",
  "canvasTable",
  "partFormat",
  "inputBinding",
  "animation",
  "actions",
]);
