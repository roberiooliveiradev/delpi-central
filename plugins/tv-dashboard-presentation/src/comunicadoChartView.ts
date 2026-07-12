import type { SeriesChartKind } from "@delpi/plugin-ui/index";

import type { ComunicadoChartType } from "./comunicadoTypes";

export function chartTypeLabel(chartType: ComunicadoChartType): string {
  const labels: Record<ComunicadoChartType, string> = {
    line: "Linhas",
    bar: "Colunas",
    area: "Área",
    stacked_bar: "Colunas empilhadas",
    pie: "Pizza",
    doughnut: "Rosca",
    scatter: "Dispersão",
    bubble: "Bolhas",
    radar: "Radar",
    combo: "Combinado",
    waterfall: "Cascata",
    funnel: "Funil",
    histogram: "Histograma",
  };
  return labels[chartType] ?? chartType;
}

export function tablePresetLabel(preset: string): string {
  if (preset === "minimal") return "Minimalista";
  if (preset === "banded") return "Faixas";
  return "Grade padrão";
}

/** Tipos com paint SVG nativo no palco (4H.7 + avançados). */
export function chartTypeHasBasicRender(chartType: ComunicadoChartType): boolean {
  return toSeriesChartKind(chartType) != null;
}

/** Mapeia tipo de bloco → kind SVG nativo (4H.7 + avançados). */
export function toSeriesChartKind(chartType: ComunicadoChartType): SeriesChartKind | null {
  switch (chartType) {
    case "line":
      return "line";
    case "bar":
      return "bar";
    case "stacked_bar":
      return "stacked_bar";
    case "histogram":
      return "histogram";
    case "area":
      return "area";
    case "pie":
    case "doughnut":
      return "pie";
    case "scatter":
      return "scatter";
    case "bubble":
      return "bubble";
    case "radar":
      return "radar";
    case "combo":
      return "combo";
    case "waterfall":
      return "waterfall";
    case "funnel":
      return "funnel";
    default:
      return null;
  }
}

/** Furo da rosca (0 = pizza cheia). */
export function pieInnerRadiusForChartType(chartType: ComunicadoChartType): number {
  return chartType === "doughnut" ? 0.55 : 0;
}

/** @deprecated Preferir `toSeriesChartKind` — mantido para widgets legados. */
export function chartTypeToLegacyDisplayMode(
  chartType: ComunicadoChartType,
): "line_chart" | "bar_chart" {
  const kind = toSeriesChartKind(chartType);
  if (
    kind === "bar" ||
    kind === "stacked_bar" ||
    kind === "histogram" ||
    kind === "waterfall"
  ) {
    return "bar_chart";
  }
  return "line_chart";
}
