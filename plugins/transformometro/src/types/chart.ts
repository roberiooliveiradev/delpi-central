export type ChartGranularity = "day" | "month" | "year";

export const CHART_GRANULARITY_OPTIONS: {
  value: ChartGranularity;
  label: string;
}[] = [
  { value: "day", label: "Dia" },
  { value: "month", label: "Mês" },
  { value: "year", label: "Ano" },
];
