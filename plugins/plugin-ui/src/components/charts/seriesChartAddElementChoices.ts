import type { SeriesChartElementId } from "./seriesChartElementCatalog";
import { chartElementPrimaryPartRef } from "./seriesChartElementCatalog";
import type { SeriesChartOptions } from "./seriesChartOptions";
import { mergeSeriesChartOptions } from "./seriesChartOptions";
import { mergeChartPartsWithOptions, type ChartPartRef, type ChartPartsMap } from "./seriesChartParts";

/** Preset do flyout «Adicionar elemento» (PPT-like, só efeitos reais). */
export type ChartAddElementChoiceId =
  | "axes:none"
  | "axes:x"
  | "axes:y"
  | "axisTitles:none"
  | "axisTitles:x"
  | "axisTitles:y"
  | "chartTitle:none"
  | "chartTitle:show"
  | "dataLabels:none"
  | "dataLabels:show"
  | "dataTable:none"
  | "dataTable:show"
  | "grid:none"
  | "grid:horizontal"
  | "grid:vertical"
  | "legend:none"
  | "legend:right"
  | "legend:top"
  | "legend:left"
  | "legend:bottom"
  | "markers:none"
  | "markers:show";

export function chartAddElementChoiceRootId(
  choiceId: ChartAddElementChoiceId,
): SeriesChartElementId {
  const root = choiceId.split(":")[0];
  if (root === "grid") return "gridlines";
  if (root === "markers") return "markers";
  if (root === "axes") return "axes";
  if (root === "axisTitles") return "axisTitles";
  if (root === "chartTitle") return "chartTitle";
  if (root === "dataLabels") return "dataLabels";
  if (root === "dataTable") return "dataTable";
  if (root === "legend") return "legend";
  return "chartTitle";
}

function axisLabelsOn(options: SeriesChartOptions, axis: "x" | "y"): boolean {
  if (options.showAxes === false) return false;
  return axis === "x" ? options.showXAxisLabels !== false : options.showYAxisLabels !== false;
}

function axisTitleOn(options: SeriesChartOptions, axis: "x" | "y"): boolean {
  return axis === "x" ? options.showXAxisTitle !== false : options.showYAxisTitle !== false;
}

/** Aplica preset flat; sincronizar parts via `applyChartAddElementChoiceWithParts`. */
export function applyChartAddElementChoice(
  choiceId: ChartAddElementChoiceId,
  options: SeriesChartOptions,
): SeriesChartOptions {
  const base = mergeSeriesChartOptions(options);

  switch (choiceId) {
    case "axes:none":
      return mergeSeriesChartOptions({
        ...base,
        showAxes: false,
        showXAxisLabels: false,
        showYAxisLabels: false,
      });
    case "axes:x": {
      const enable = !axisLabelsOn(base, "x");
      const yOn = axisLabelsOn(base, "y");
      return mergeSeriesChartOptions({
        ...base,
        showAxes: enable || yOn,
        showXAxisLabels: enable,
        showYAxisLabels: yOn,
      });
    }
    case "axes:y": {
      const enable = !axisLabelsOn(base, "y");
      const xOn = axisLabelsOn(base, "x");
      return mergeSeriesChartOptions({
        ...base,
        showAxes: enable || xOn,
        showXAxisLabels: xOn,
        showYAxisLabels: enable,
      });
    }
    case "axisTitles:none":
      return mergeSeriesChartOptions({
        ...base,
        showXAxisTitle: false,
        showYAxisTitle: false,
      });
    case "axisTitles:x": {
      const enable = !axisTitleOn(base, "x");
      return mergeSeriesChartOptions({ ...base, showXAxisTitle: enable });
    }
    case "axisTitles:y": {
      const enable = !axisTitleOn(base, "y");
      return mergeSeriesChartOptions({ ...base, showYAxisTitle: enable });
    }
    case "chartTitle:none":
      return mergeSeriesChartOptions({ ...base, showTitle: false });
    case "chartTitle:show":
      return mergeSeriesChartOptions({ ...base, showTitle: true });
    case "dataLabels:none":
      return mergeSeriesChartOptions({ ...base, showDataLabels: false });
    case "dataLabels:show":
      return mergeSeriesChartOptions({ ...base, showDataLabels: true });
    case "dataTable:none":
      return mergeSeriesChartOptions({ ...base, showDataTable: false });
    case "dataTable:show":
      return mergeSeriesChartOptions({ ...base, showDataTable: true });
    case "grid:none":
      return mergeSeriesChartOptions({
        ...base,
        showGrid: false,
        showVerticalGrid: false,
      });
    case "grid:horizontal":
      return mergeSeriesChartOptions({
        ...base,
        showGrid: base.showGrid === false,
      });
    case "grid:vertical":
      return mergeSeriesChartOptions({
        ...base,
        showVerticalGrid: !Boolean(base.showVerticalGrid),
      });
    case "legend:none":
      return mergeSeriesChartOptions({
        ...base,
        showLegend: false,
        legendPosition: "hidden",
      });
    case "legend:right":
      return mergeSeriesChartOptions({
        ...base,
        showLegend: true,
        legendPosition: "right",
      });
    case "legend:top":
      return mergeSeriesChartOptions({
        ...base,
        showLegend: true,
        legendPosition: "top",
      });
    case "legend:left":
      return mergeSeriesChartOptions({
        ...base,
        showLegend: true,
        legendPosition: "left",
      });
    case "legend:bottom":
      return mergeSeriesChartOptions({
        ...base,
        showLegend: true,
        legendPosition: "bottom",
      });
    case "markers:none":
      return mergeSeriesChartOptions({ ...base, showMarkers: false });
    case "markers:show":
      return mergeSeriesChartOptions({ ...base, showMarkers: true });
    default: {
      const _exhaustive: never = choiceId;
      return _exhaustive;
    }
  }
}

export function applyChartAddElementChoiceWithParts(
  choiceId: ChartAddElementChoiceId,
  options: SeriesChartOptions,
  parts?: ChartPartsMap | null,
): { options: SeriesChartOptions; parts: ChartPartsMap } {
  const nextOptions = applyChartAddElementChoice(choiceId, options);
  return {
    options: nextOptions,
    parts: mergeChartPartsWithOptions(parts, nextOptions),
  };
}

export function isChartAddElementChoiceActive(
  choiceId: ChartAddElementChoiceId,
  options: SeriesChartOptions,
): boolean {
  const base = mergeSeriesChartOptions(options);
  switch (choiceId) {
    case "axes:none":
      return !axisLabelsOn(base, "x") && !axisLabelsOn(base, "y");
    case "axes:x":
      return axisLabelsOn(base, "x");
    case "axes:y":
      return axisLabelsOn(base, "y");
    case "axisTitles:none":
      return !axisTitleOn(base, "x") && !axisTitleOn(base, "y");
    case "axisTitles:x":
      return axisTitleOn(base, "x");
    case "axisTitles:y":
      return axisTitleOn(base, "y");
    case "chartTitle:none":
      return base.showTitle === false;
    case "chartTitle:show":
      return base.showTitle !== false;
    case "dataLabels:none":
      return !base.showDataLabels;
    case "dataLabels:show":
      return Boolean(base.showDataLabels);
    case "dataTable:none":
      return !base.showDataTable;
    case "dataTable:show":
      return Boolean(base.showDataTable);
    case "grid:none":
      return base.showGrid === false && !base.showVerticalGrid;
    case "grid:horizontal":
      return base.showGrid !== false;
    case "grid:vertical":
      return Boolean(base.showVerticalGrid);
    case "legend:none":
      return base.showLegend === false || base.legendPosition === "hidden";
    case "legend:right":
      return base.showLegend !== false && base.legendPosition === "right";
    case "legend:top":
      return base.showLegend !== false && base.legendPosition === "top";
    case "legend:left":
      return base.showLegend !== false && base.legendPosition === "left";
    case "legend:bottom":
      return (
        base.showLegend !== false &&
        (base.legendPosition === "bottom" || base.legendPosition == null)
      );
    case "markers:none":
      return base.showMarkers === false;
    case "markers:show":
      return base.showMarkers !== false;
    default: {
      const _exhaustive: never = choiceId;
      return _exhaustive;
    }
  }
}

export function chartAddElementMoreOptionsPartRef(
  elementId: SeriesChartElementId,
): ChartPartRef | null {
  return chartElementPrimaryPartRef(elementId);
}
