export type ChartGranularity = "day" | "week" | "month" | "year";

export type ChartSeriesPoint = {
  periodo: string;
  sortKey: string;
  dateStart: string;
  dateEnd: string;
  value: number;
};

export const CHART_GRANULARITY_OPTIONS: {
  value: ChartGranularity;
  label: string;
}[] = [
  { value: "day", label: "Dia" },
  { value: "week", label: "Semana" },
  { value: "month", label: "Mês" },
  { value: "year", label: "Ano" },
];
