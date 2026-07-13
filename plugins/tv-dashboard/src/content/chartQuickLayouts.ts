import {
  applyChartElementVisibility,
  type ChartElementId,
  type ComunicadoChartOptions,
  type ComunicadoChartPartsMap,
} from "@delpi/tv-dashboard-presentation";

export type ChartQuickLayoutId =
  | "title_legend_bottom"
  | "title_legend_right"
  | "title_axes"
  | "minimal"
  | "full_with_table";

export type ChartQuickLayout = {
  id: ChartQuickLayoutId;
  label: string;
  /** Wireframe hint for thumb aria. */
  hint: string;
  elements: Partial<Record<ChartElementId, boolean>>;
  legendPosition?: NonNullable<ComunicadoChartOptions["legendPosition"]>;
};

/** Presets declarativos — Layout Rápido (PPT/Excel). */
export const CHART_QUICK_LAYOUTS: ChartQuickLayout[] = [
  {
    id: "title_legend_bottom",
    label: "Título + legenda inferior",
    hint: "Título, eixos, grade e legenda embaixo.",
    elements: {
      chartTitle: true,
      legend: true,
      axisTitles: true,
      axes: true,
      gridlines: true,
      dataLabels: false,
      dataTable: false,
    },
    legendPosition: "bottom",
  },
  {
    id: "title_legend_right",
    label: "Título + legenda à direita",
    hint: "Título e legenda à direita do gráfico.",
    elements: {
      chartTitle: true,
      legend: true,
      axisTitles: true,
      axes: true,
      gridlines: true,
      dataLabels: false,
      dataTable: false,
    },
    legendPosition: "right",
  },
  {
    id: "title_axes",
    label: "Título e eixos",
    hint: "Sem legenda — foco em eixos e grade.",
    elements: {
      chartTitle: true,
      legend: false,
      axisTitles: true,
      axes: true,
      gridlines: true,
      dataLabels: false,
      dataTable: false,
    },
  },
  {
    id: "minimal",
    label: "Mínimo",
    hint: "Só a série — sem título, legenda ou tabela.",
    elements: {
      chartTitle: false,
      legend: false,
      axisTitles: false,
      axes: true,
      gridlines: false,
      dataLabels: false,
      dataTable: false,
    },
  },
  {
    id: "full_with_table",
    label: "Completo + tabela",
    hint: "Título, legenda, eixos e tabela de dados.",
    elements: {
      chartTitle: true,
      legend: true,
      axisTitles: true,
      axes: true,
      gridlines: true,
      dataLabels: false,
      dataTable: true,
    },
    legendPosition: "bottom",
  },
];

export function applyChartQuickLayout(
  layout: ChartQuickLayout,
  options: ComunicadoChartOptions,
  parts?: ComunicadoChartPartsMap | null,
): { options: ComunicadoChartOptions; parts: ComunicadoChartPartsMap } {
  let nextOptions = { ...options };
  let nextParts = parts ?? {};

  for (const [elementId, enabled] of Object.entries(layout.elements) as Array<
    [ChartElementId, boolean]
  >) {
    if (typeof enabled !== "boolean") continue;
    const result = applyChartElementVisibility(elementId, enabled, nextOptions, nextParts);
    nextOptions = result.options;
    nextParts = result.parts;
  }

  if (layout.legendPosition && nextOptions.showLegend !== false) {
    nextOptions = {
      ...nextOptions,
      showLegend: true,
      legendPosition: layout.legendPosition,
    };
  }

  return { options: nextOptions, parts: nextParts };
}
