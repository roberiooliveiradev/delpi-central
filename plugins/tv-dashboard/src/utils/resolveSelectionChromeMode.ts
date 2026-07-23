import type {
  ComunicadoBlock,
  ComunicadoChartPartRef,
  ComunicadoInputPartRef,
  ComunicadoKpiPartRef,
  ComunicadoTablePartRef,
} from "@delpi/tv-dashboard-presentation";
import {
  serializeChartPartRef,
  serializeInputPartRef,
  serializeKpiPartRef,
  serializeTablePartRef,
} from "@delpi/tv-dashboard-presentation";

export type SelectionChromeSource = "chart" | "kpi" | "table" | "input";

export type SelectionChromeMode =
  | { mode: "block" }
  | {
      mode: "part";
      source: SelectionChromeSource;
      partLabel: string;
      /** Rótulo do botão Voltar (ex.: «Voltar ao gráfico»). */
      backLabel: string;
      /** Nome curto do bloco-pai na dica da ribbon. */
      parentLabel: string;
    };

export function chartPartSelectionLabel(part: ComunicadoChartPartRef): string {
  switch (part.kind) {
    case "chartArea":
      return "Área do gráfico";
    case "plotArea":
      return "Área de plotagem";
    case "title":
      return "Título";
    case "legend":
      return "Legenda";
    case "series":
      return `Série ${(part.seriesIndex ?? 0) + 1}`;
    case "marker":
      return `Marcador série ${(part.seriesIndex ?? 0) + 1} · ponto ${(part.pointIndex ?? 0) + 1}`;
    case "dataLabel":
      return `Rótulo ${(part.pointIndex ?? 0) + 1}`;
    case "dataLabels":
      return "Rótulos de dados";
    case "axes":
      return "Eixos";
    case "axis":
      return part.axis === "x" ? "Eixo X" : "Eixo Y";
    case "axisTitle":
      return part.axis === "x" ? "Título eixo X" : "Título eixo Y";
    case "grid":
      return "Grade";
    case "dataTable":
      return "Tabela de dados";
    default:
      return serializeChartPartRef(part);
  }
}

export function kpiPartSelectionLabel(part: ComunicadoKpiPartRef): string {
  switch (part.kind) {
    case "card":
      return "Card";
    case "title":
      return "Título";
    case "value":
      return "Valor";
    case "hint":
      return "Subtítulo";
    case "icon":
      return "Ícone";
    case "comparison":
      return "Comparação";
    case "progress":
      return "Progresso";
    case "sparkline":
      return "Sparkline";
    case "metricCard":
      return `Métrica · ${part.field}`;
    default:
      return serializeKpiPartRef(part);
  }
}

export function tablePartSelectionLabel(part: ComunicadoTablePartRef): string {
  switch (part.kind) {
    case "frame":
      return "Moldura";
    case "title":
      return "Título";
    case "header":
      return "Cabeçalho";
    case "headerCell":
      return `Coluna ${(part.colIndex ?? 0) + 1}`;
    case "cell":
      return `Célula ${(part.rowIndex ?? 0) + 1}:${(part.colIndex ?? 0) + 1}`;
    default:
      return serializeTablePartRef(part);
  }
}

export function inputPartSelectionLabel(part: ComunicadoInputPartRef): string {
  switch (part.kind) {
    case "frame":
      return "Moldura";
    case "icon":
      return "Ícone";
    case "label":
      return "Rótulo";
    case "badge":
      return "Badge de escopo";
    case "control":
      return "Controle";
    default:
      return serializeInputPartRef(part);
  }
}

/**
 * Decide chrome de ribbon/painel: bloco inteiro vs parte interna.
 * Uma regra para gráfico, KPI, tabela e filtro — sem misturar controles globais com item.
 */
export function resolveSelectionChromeMode(params: {
  selected: ComunicadoBlock | null;
  selectedChartPart?: ComunicadoChartPartRef | null;
  selectedKpiPart?: ComunicadoKpiPartRef | null;
  selectedTablePart?: ComunicadoTablePartRef | null;
  selectedInputPart?: ComunicadoInputPartRef | null;
}): SelectionChromeMode {
  const {
    selected,
    selectedChartPart = null,
    selectedKpiPart = null,
    selectedTablePart = null,
    selectedInputPart = null,
  } = params;
  if (!selected) return { mode: "block" };

  if (selected.type === "chart_view" && selectedChartPart) {
    return {
      mode: "part",
      source: "chart",
      partLabel: chartPartSelectionLabel(selectedChartPart),
      backLabel: "Voltar ao gráfico",
      parentLabel: "Gráfico",
    };
  }

  if (selected.type === "kpi_view" && selectedKpiPart) {
    return {
      mode: "part",
      source: "kpi",
      partLabel: kpiPartSelectionLabel(selectedKpiPart),
      backLabel: "Voltar ao KPI",
      parentLabel: "KPI",
    };
  }

  if (selected.type === "table_view" && selectedTablePart) {
    return {
      mode: "part",
      source: "table",
      partLabel: tablePartSelectionLabel(selectedTablePart),
      backLabel: "Voltar à tabela",
      parentLabel: "Tabela",
    };
  }

  if (selected.type === "input" && selectedInputPart) {
    return {
      mode: "part",
      source: "input",
      partLabel: inputPartSelectionLabel(selectedInputPart),
      backLabel: "Voltar ao filtro",
      parentLabel: "Filtro",
    };
  }

  return { mode: "block" };
}

export function isPartSelectionChrome(mode: SelectionChromeMode): mode is Extract<
  SelectionChromeMode,
  { mode: "part" }
> {
  return mode.mode === "part";
}
