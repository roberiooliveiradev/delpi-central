import {
  serializeChartPartRef,
  type ComunicadoChartPartRef,
  type ComunicadoChartViewBlock,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiViewBlock,
  type ComunicadoTablePartRef,
  type ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";

import {
  chartPartSelectionLabel,
  kpiPartSelectionLabel,
  tablePartSelectionLabel,
} from "./resolveSelectionChromeMode";

export type ActivePartOption = {
  value: string;
  label: string;
  chartPart?: ComunicadoChartPartRef;
  kpiPart?: ComunicadoKpiPartRef;
  tablePart?: ComunicadoTablePartRef;
};

/** Opções do dropdown «Elemento ativo» (estilo Excel). */
export function listChartActivePartOptions(block: ComunicadoChartViewBlock): ActivePartOption[] {
  const series = block.chartProjection?.series ?? [];
  const seriesCount = Math.max(series.length, 1);
  const options: ActivePartOption[] = [
    { value: "chartArea", label: "Área do gráfico", chartPart: { kind: "chartArea" } },
    { value: "plotArea", label: "Área de plotagem", chartPart: { kind: "plotArea" } },
    { value: "title", label: "Título", chartPart: { kind: "title" } },
    { value: "legend", label: "Legenda", chartPart: { kind: "legend" } },
    { value: "axis:x", label: "Eixo X", chartPart: { kind: "axis", axis: "x" } },
    { value: "axis:y", label: "Eixo Y", chartPart: { kind: "axis", axis: "y" } },
    { value: "axisTitle:x", label: "Título eixo X", chartPart: { kind: "axisTitle", axis: "x" } },
    { value: "axisTitle:y", label: "Título eixo Y", chartPart: { kind: "axisTitle", axis: "y" } },
    { value: "grid", label: "Grade", chartPart: { kind: "grid" } },
  ];
  for (let i = 0; i < seriesCount; i += 1) {
    const label =
      series[i]?.label?.trim() ||
      series[i]?.field?.trim() ||
      `Série ${i + 1}`;
    options.push({
      value: `series:${i}`,
      label: `Série «${label}»`,
      chartPart: { kind: "series", seriesIndex: i },
    });
  }
  return options;
}

export function listKpiActivePartOptions(block: ComunicadoKpiViewBlock): ActivePartOption[] {
  const metrics = block.kpiProjection?.metrics ?? [];
  const options: ActivePartOption[] = [
    { value: "card", label: "Card", kpiPart: { kind: "card" } },
    { value: "title", label: "Título", kpiPart: { kind: "title" } },
    { value: "value", label: "Valor", kpiPart: { kind: "value" } },
    { value: "hint", label: "Subtítulo", kpiPart: { kind: "hint" } },
    { value: "icon", label: "Ícone", kpiPart: { kind: "icon" } },
  ];
  for (const metric of metrics) {
    const field = metric.field?.trim();
    if (!field) continue;
    options.push({
      value: `metricCard:${field}`,
      label: `Métrica · ${metric.label?.trim() || field}`,
      kpiPart: { kind: "metricCard", field },
    });
  }
  return options;
}

export function listTableActivePartOptions(block: ComunicadoTableViewBlock): ActivePartOption[] {
  const options: ActivePartOption[] = [
    { value: "frame", label: "Moldura", tablePart: { kind: "frame" } },
    { value: "title", label: "Título", tablePart: { kind: "title" } },
    { value: "header", label: "Cabeçalho", tablePart: { kind: "header" } },
  ];
  const projected = (block.tableProjection?.columns ?? []).filter((col) => col.visible !== false);
  const resolvedCols = block.resolved?.table?.columns ?? [];
  if (projected.length > 0) {
    projected.forEach((col, colIndex) => {
      options.push({
        value: `headerCell:${colIndex}`,
        label: `Coluna · ${col.label?.trim() || col.key}`,
        tablePart: { kind: "headerCell", colIndex },
      });
    });
  } else {
    resolvedCols.forEach((col, colIndex) => {
      options.push({
        value: `headerCell:${colIndex}`,
        label: `Coluna · ${col.label?.trim() || col.key}`,
        tablePart: { kind: "headerCell", colIndex },
      });
    });
  }
  return options;
}

export function activePartOptionValue(params: {
  chartPart?: ComunicadoChartPartRef | null;
  kpiPart?: ComunicadoKpiPartRef | null;
  tablePart?: ComunicadoTablePartRef | null;
}): string {
  if (params.chartPart) return serializeChartPartRef(params.chartPart);
  if (params.kpiPart) {
    if (params.kpiPart.kind === "metricCard") return `metricCard:${params.kpiPart.field}`;
    return params.kpiPart.kind;
  }
  if (params.tablePart) return params.tablePart.kind;
  return "";
}

export function activePartOptionLabel(option: ActivePartOption): string {
  if (option.chartPart) return option.label || chartPartSelectionLabel(option.chartPart);
  if (option.kpiPart) return option.label || kpiPartSelectionLabel(option.kpiPart);
  if (option.tablePart) return option.label || tablePartSelectionLabel(option.tablePart);
  return option.label;
}
