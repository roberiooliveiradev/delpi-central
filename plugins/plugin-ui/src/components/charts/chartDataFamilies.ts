import type { PersistedChartType } from "../../hooks/usePersistedChartPreferences";

export type ChartDataFamily =
  | "time_multi_series"
  | "period_compare"
  | "ranking"
  | "composition"
  | "categorical"
  | "funnel"
  | "scalar"
  | "mini";

export const TIME_MULTI_SERIES_TYPES = ["column", "line", "area"] as const satisfies readonly PersistedChartType[];
export const PERIOD_COMPARE_TYPES = ["column", "line", "area"] as const satisfies readonly PersistedChartType[];
export const RANKING_TYPES = ["horizontal_bar", "bar", "pie"] as const satisfies readonly PersistedChartType[];
export const COMPOSITION_TYPES = ["stacked_bar"] as const satisfies readonly PersistedChartType[];
export const CATEGORICAL_TYPES = ["bar"] as const satisfies readonly PersistedChartType[];

const FAMILY_TYPES: Record<ChartDataFamily, readonly PersistedChartType[]> = {
  time_multi_series: TIME_MULTI_SERIES_TYPES,
  period_compare: PERIOD_COMPARE_TYPES,
  ranking: RANKING_TYPES,
  composition: COMPOSITION_TYPES,
  categorical: CATEGORICAL_TYPES,
  funnel: [],
  scalar: [],
  mini: [],
};

export const CHART_TYPE_LABELS_PT: Record<PersistedChartType, string> = {
  column: "Colunas",
  line: "Linhas",
  area: "Área",
  pie: "Pizza",
  bar: "Barras",
  horizontal_bar: "Horiz.",
  stacked_bar: "Empilhado",
};

export function chartTypesForFamily(
  family: ChartDataFamily,
  options?: { categoryCount?: number },
): readonly PersistedChartType[] {
  const base = FAMILY_TYPES[family] ?? [];
  if (family === "ranking" && options?.categoryCount != null && options.categoryCount > 12) {
    return base.filter((type) => type !== "pie");
  }
  return base;
}

export function defaultChartTypeForFamily(family: ChartDataFamily): PersistedChartType | undefined {
  const types = FAMILY_TYPES[family];
  if (!types.length) return undefined;
  if (family === "time_multi_series") return "column";
  if (family === "ranking") return "horizontal_bar";
  return types[0];
}

export function familySupportsChartTypeSwitch(family: ChartDataFamily): boolean {
  return (FAMILY_TYPES[family]?.length ?? 0) > 1;
}
