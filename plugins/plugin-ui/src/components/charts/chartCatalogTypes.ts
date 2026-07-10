/** Tipos de gráfico disponíveis no catálogo de inserção (estilo PowerPoint/Excel). */
export type DelpiChartType =
  | "line"
  | "bar"
  | "area"
  | "stacked_bar"
  | "pie"
  | "doughnut"
  | "scatter"
  | "bubble"
  | "radar"
  | "combo"
  | "waterfall"
  | "funnel"
  | "histogram";

export type DelpiChartCatalogCategory = "series" | "comparison" | "distribution" | "special";

export type DelpiChartCatalogEntry = {
  type: DelpiChartType;
  label: string;
  category: DelpiChartCatalogCategory;
  /** Nome do ícone Lucide (renderizado pelo painel). */
  icon: string;
};

export const DELPI_CHART_CATALOG_CATEGORIES: Array<{ id: DelpiChartCatalogCategory; label: string }> = [
  { id: "series", label: "Séries" },
  { id: "comparison", label: "Comparação" },
  { id: "distribution", label: "Distribuição" },
  { id: "special", label: "Especiais" },
];

export const DELPI_CHART_TYPE_CATALOG: DelpiChartCatalogEntry[] = [
  { type: "line", label: "Linhas", category: "series", icon: "LineChart" },
  { type: "area", label: "Área", category: "series", icon: "AreaChart" },
  { type: "bar", label: "Colunas", category: "comparison", icon: "BarChart3" },
  { type: "stacked_bar", label: "Colunas empilhadas", category: "comparison", icon: "BarChart4" },
  { type: "histogram", label: "Histograma", category: "distribution", icon: "ChartColumn" },
  { type: "pie", label: "Pizza", category: "distribution", icon: "PieChart" },
  { type: "doughnut", label: "Rosca", category: "distribution", icon: "CircleDot" },
  { type: "scatter", label: "Dispersão", category: "distribution", icon: "ScatterChart" },
  { type: "bubble", label: "Bolhas", category: "distribution", icon: "Circle" },
  { type: "radar", label: "Radar", category: "special", icon: "Radar" },
  { type: "combo", label: "Combinado", category: "special", icon: "ChartSpline" },
  { type: "waterfall", label: "Cascata", category: "special", icon: "ChartNoAxesColumnIncreasing" },
  { type: "funnel", label: "Funil", category: "special", icon: "Filter" },
];

export type DelpiTableInsertPreset = "grid" | "minimal" | "banded";

export type DelpiTableInsertSelection = {
  rows: number;
  cols: number;
  preset: DelpiTableInsertPreset;
};

export const DELPI_TABLE_GRID_MAX_ROWS = 10;
export const DELPI_TABLE_GRID_MAX_COLS = 8;

export const DELPI_TABLE_INSERT_PRESETS: Array<{ id: DelpiTableInsertPreset; label: string; hint: string }> = [
  { id: "grid", label: "Grade padrão", hint: "Tabela com cabeçalho e linhas alternadas." },
  { id: "minimal", label: "Minimalista", hint: "Sem faixas alternadas — só bordas leves." },
  { id: "banded", label: "Faixas", hint: "Linhas zebradas para leitura longa." },
];
