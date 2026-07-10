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

/** Tipos com render SVG básico no palco (demais exibem placeholder estilizado). */
export function chartTypeHasBasicRender(chartType: ComunicadoChartType): boolean {
  return chartType === "line" || chartType === "bar" || chartType === "area" || chartType === "stacked_bar";
}

export function chartTypeToLegacyDisplayMode(
  chartType: ComunicadoChartType,
): "line_chart" | "bar_chart" {
  if (chartType === "bar" || chartType === "stacked_bar" || chartType === "histogram") {
    return "bar_chart";
  }
  return "line_chart";
}
