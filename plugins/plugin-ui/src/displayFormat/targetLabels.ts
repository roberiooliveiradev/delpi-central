import type { DisplayFormatTarget } from "./types";

export const DISPLAY_FORMAT_TARGET_LABELS: Record<DisplayFormatTarget, string> = {
  chartValue: "Valores do gráfico",
  chartCategory: "Eixo X (categorias / datas)",
  table: "Grade inteira",
  kpi: "KPI",
  canvasCell: "Célula",
};

export function resolveDisplayFormatTargetLabel(target: DisplayFormatTarget): string {
  return DISPLAY_FORMAT_TARGET_LABELS[target];
}
