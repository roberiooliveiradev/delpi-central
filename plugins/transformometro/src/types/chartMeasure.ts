export type ChartMeasure = "currency" | "hours";

export const CHART_MEASURE_OPTIONS: { value: ChartMeasure; label: string }[] = [
  { value: "currency", label: "R$" },
  { value: "hours", label: "Horas" },
];
