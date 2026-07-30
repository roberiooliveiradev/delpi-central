export type ChartGranularity = "day" | "week" | "month" | "year";

export const CHART_GRANULARITY_OPTIONS: {
  value: ChartGranularity;
  label: string;
}[] = [
  { value: "day", label: "Dia" },
  { value: "week", label: "Semana" },
  { value: "month", label: "Mês" },
  { value: "year", label: "Ano" },
];
