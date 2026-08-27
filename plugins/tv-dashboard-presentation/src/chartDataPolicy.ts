/**
 * Políticas de encoding por tipo de gráfico (Playbook CHART-DATA-POLICIES).
 * Declara wells, rowMode e agregação default — o builder em viewProjection consome.
 */

import type { ComunicadoChartType } from "./comunicadoTypes";
import type { ViewAggregation } from "./fieldValueProjection";

export type ChartDataRowMode = "rowwise" | "groupByCategory" | "bins";

export type ChartDataWellRole =
  | "category"
  | "value"
  | "series"
  | "xMeasure"
  | "yMeasure"
  | "size"
  | "goal";

export type ChartDataWellSpec = {
  id: string;
  role: ChartDataWellRole;
  /** Rótulo PT no painel Dados. */
  label: string;
  valueKind: "category" | "measure";
  required?: boolean;
};

export type ChartDataPolicy = {
  chartType: ComunicadoChartType;
  family: "series" | "comparison" | "distribution" | "special";
  rowMode: ChartDataRowMode;
  /** Agregação ao agrupar / quando a medida não tem valor finito nas linhas. */
  defaultAggregation: ViewAggregation;
  /** Máx. de séries Y sugeridas no default. */
  maxSeries: number;
  wells: ChartDataWellSpec[];
  /** Soft cap de categorias (fatias / barras). */
  maxCategories?: number;
};

const WELL_CATEGORY: ChartDataWellSpec = {
  id: "category",
  role: "category",
  label: "Categoria",
  valueKind: "category",
  required: true,
};

const WELL_VALUE: ChartDataWellSpec = {
  id: "value",
  role: "value",
  label: "Valor",
  valueKind: "measure",
};

const WELL_SERIES: ChartDataWellSpec = {
  id: "series",
  role: "series",
  label: "Séries (Y)",
  valueKind: "measure",
};

const WELL_X_AXIS: ChartDataWellSpec = {
  id: "category",
  role: "category",
  label: "Eixo X",
  valueKind: "category",
};

const WELL_X_MEASURE: ChartDataWellSpec = {
  id: "xMeasure",
  role: "xMeasure",
  label: "X (medida)",
  valueKind: "measure",
  required: true,
};

const WELL_Y_MEASURE: ChartDataWellSpec = {
  id: "yMeasure",
  role: "yMeasure",
  label: "Y (medida)",
  valueKind: "measure",
  required: true,
};

const WELL_SIZE: ChartDataWellSpec = {
  id: "size",
  role: "size",
  label: "Tamanho",
  valueKind: "measure",
};

/** Meta escalar a partir de coluna (não vira série de legenda). */
export const WELL_GOAL: ChartDataWellSpec = {
  id: "goal",
  role: "goal",
  label: "Meta",
  valueKind: "measure",
};

/** Tipos com linha de meta / by_goal + velocímetro. */
const CHART_TYPES_WITH_GOAL_WELL: ComunicadoChartType[] = [
  "line",
  "area",
  "bar",
  "horizontal_bar",
  "stacked_bar",
  "combo",
  "histogram",
  "scatter",
  "bubble",
  "radar",
  "waterfall",
  "gauge",
];

function withOptionalGoal(wells: ChartDataWellSpec[], chartType: ComunicadoChartType): ChartDataWellSpec[] {
  if (!CHART_TYPES_WITH_GOAL_WELL.includes(chartType)) return wells;
  if (wells.some((well) => well.role === "goal")) return wells;
  return [...wells, WELL_GOAL];
}

const POLICIES_BASE: Record<ComunicadoChartType, ChartDataPolicy> = {
  line: {
    chartType: "line",
    family: "series",
    rowMode: "rowwise",
    defaultAggregation: "first",
    maxSeries: 6,
    wells: [WELL_X_AXIS, WELL_SERIES],
  },
  area: {
    chartType: "area",
    family: "series",
    rowMode: "rowwise",
    defaultAggregation: "first",
    maxSeries: 6,
    wells: [WELL_X_AXIS, WELL_SERIES],
  },
  bar: {
    chartType: "bar",
    family: "comparison",
    rowMode: "groupByCategory",
    defaultAggregation: "sum",
    maxSeries: 6,
    /* Sem teto: CTs / dimensões operacionais precisam aparecer todos (não «Outros»). */
    wells: [WELL_CATEGORY, WELL_SERIES],
  },
  horizontal_bar: {
    chartType: "horizontal_bar",
    family: "comparison",
    rowMode: "groupByCategory",
    defaultAggregation: "sum",
    maxSeries: 6,
    wells: [WELL_CATEGORY, WELL_SERIES],
  },
  stacked_bar: {
    chartType: "stacked_bar",
    family: "comparison",
    rowMode: "groupByCategory",
    defaultAggregation: "sum",
    maxSeries: 6,
    wells: [WELL_CATEGORY, WELL_SERIES],
  },
  pie: {
    chartType: "pie",
    family: "distribution",
    rowMode: "groupByCategory",
    /** Medida numérica → soma por fatia (Excel/Power BI). Contagem só sem medida. */
    defaultAggregation: "sum",
    maxSeries: 1,
    maxCategories: 8,
    wells: [WELL_CATEGORY, WELL_VALUE],
  },
  doughnut: {
    chartType: "doughnut",
    family: "distribution",
    rowMode: "groupByCategory",
    defaultAggregation: "sum",
    maxSeries: 1,
    maxCategories: 8,
    wells: [WELL_CATEGORY, WELL_VALUE],
  },
  histogram: {
    chartType: "histogram",
    family: "distribution",
    rowMode: "bins",
    defaultAggregation: "first",
    maxSeries: 1,
    wells: [{ id: "value", role: "value", label: "Medida", valueKind: "measure", required: true }],
  },
  scatter: {
    chartType: "scatter",
    family: "distribution",
    rowMode: "rowwise",
    defaultAggregation: "first",
    maxSeries: 1,
    wells: [WELL_X_MEASURE, WELL_Y_MEASURE],
  },
  bubble: {
    chartType: "bubble",
    family: "distribution",
    rowMode: "rowwise",
    defaultAggregation: "first",
    /** Y + size (size não é overlay de legenda — ver buildSeriesFromTable). */
    maxSeries: 2,
    wells: [WELL_X_MEASURE, WELL_Y_MEASURE, WELL_SIZE],
  },
  radar: {
    chartType: "radar",
    family: "special",
    rowMode: "groupByCategory",
    defaultAggregation: "avg",
    maxSeries: 4,
    maxCategories: 12,
    wells: [WELL_CATEGORY, WELL_SERIES],
  },
  combo: {
    chartType: "combo",
    family: "special",
    rowMode: "groupByCategory",
    defaultAggregation: "sum",
    maxSeries: 4,
    wells: [WELL_CATEGORY, WELL_SERIES],
  },
  waterfall: {
    chartType: "waterfall",
    family: "special",
    rowMode: "groupByCategory",
    defaultAggregation: "sum",
    maxSeries: 1,
    maxCategories: 16,
    wells: [WELL_CATEGORY, WELL_VALUE],
  },
  funnel: {
    chartType: "funnel",
    family: "special",
    rowMode: "groupByCategory",
    defaultAggregation: "sum",
    maxSeries: 1,
    maxCategories: 12,
    wells: [WELL_CATEGORY, WELL_VALUE],
  },
  gauge: {
    chartType: "gauge",
    family: "special",
    rowMode: "rowwise",
    defaultAggregation: "first",
    maxSeries: 1,
    wells: [
      { id: "value", role: "value", label: "Valor", valueKind: "measure", required: true },
    ],
  },
};

const POLICIES: Record<ComunicadoChartType, ChartDataPolicy> = Object.fromEntries(
  (Object.keys(POLICIES_BASE) as ComunicadoChartType[]).map((chartType) => {
    const base = POLICIES_BASE[chartType];
    return [
      chartType,
      {
        ...base,
        wells: withOptionalGoal(base.wells, chartType),
      },
    ];
  }),
) as Record<ComunicadoChartType, ChartDataPolicy>;

export function resolveChartDataPolicy(chartType: ComunicadoChartType): ChartDataPolicy {
  return POLICIES[chartType] ?? POLICIES.line;
}

export function chartPolicyHasGoalWell(chartType: ComunicadoChartType): boolean {
  return resolveChartDataPolicy(chartType).wells.some((well) => well.role === "goal");
}

/** Hint do painel Dados conforme a policy. */
export function chartAxesEditorHint(policy: ChartDataPolicy, hasProjection: boolean): string {
  if (policy.chartType === "gauge") {
    return hasProjection
      ? "Valor = agulha do velocímetro; Meta (opcional) = coluna do mesmo modelo."
      : "Escolha a medida do valor e, se quiser, a coluna de meta.";
  }
  if (policy.chartType === "pie" || policy.chartType === "doughnut") {
    return hasProjection
      ? "Categoria = fatias; Valor = ângulo (agregado por categoria)."
      : "Escolha a categoria (ex.: Tipo) e o valor — ou só a categoria para contar linhas.";
  }
  if (policy.chartType === "scatter" || policy.chartType === "bubble") {
    return hasProjection
      ? "X e Y são medidas numéricas (um ponto por linha)."
      : "Escolha duas medidas numéricas para X e Y.";
  }
  if (policy.chartType === "histogram") {
    return hasProjection
      ? "Uma medida contínua — o gráfico agrupa em faixas."
      : "Escolha a medida numérica do histograma.";
  }
  if (policy.rowMode === "groupByCategory") {
    return hasProjection
      ? "Categoria de referência; valores agregados por categoria."
      : "Escolha a categoria e as séries (valores são agregados).";
  }
  return hasProjection
    ? "X = categoria de referência; Y = séries (arraste para ordenar)."
    : "Automático (série da rota). Escolha a categoria X e as séries Y.";
}

export function chartCategoryWellLabel(policy: ChartDataPolicy): string {
  const well = policy.wells.find((item) => item.role === "category" || item.role === "xMeasure");
  return well?.label ?? "Categoria (X)";
}

export function chartSeriesWellLabel(policy: ChartDataPolicy): string {
  const well = policy.wells.find(
    (item) =>
      item.role === "value" ||
      item.role === "series" ||
      item.role === "yMeasure",
  );
  return well?.label ?? "Séries (Y)";
}

export function chartGoalWellLabel(policy: ChartDataPolicy): string {
  return policy.wells.find((item) => item.role === "goal")?.label ?? "Meta";
}

/**
 * Agregação ao marcar uma série no painel Dados.
 * Campo textual/data → contagem; medida → default da policy (soma em pizza/barra).
 */
export function resolveChartSeriesDefaultAggregation(
  policy: ChartDataPolicy,
  fieldType?: "number" | "string" | "date" | null,
): ViewAggregation {
  if (fieldType === "string" || fieldType === "date") return "count";
  return policy.defaultAggregation;
}
