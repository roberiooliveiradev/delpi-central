import type { ChatPresentation } from "../../data/api/chatTypes";

type ChartPresentation = Extract<ChatPresentation, { type: "chart" }>;

type LegacyChartPayload = ChartPresentation & {
  labels?: string[];
  datasets?: Array<{ label?: string; data?: number[] }>;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** Converte payload legado (labels/datasets) para o formato `data[]` do ChatRichChart. */
export function normalizeChartPresentation(value: unknown): ChartPresentation | null {
  if (!isRecord(value) || value.type !== "chart") {
    return null;
  }

  const chart = value as LegacyChartPayload;
  const existingData = Array.isArray(chart.data) ? chart.data : [];

  if (existingData.length > 0) {
    return chart;
  }

  const labels = Array.isArray(chart.labels) ? chart.labels : [];
  const dataset = Array.isArray(chart.datasets) ? chart.datasets[0] : undefined;
  const values = Array.isArray(dataset?.data) ? dataset.data : [];

  if (!labels.length || labels.length !== values.length) {
    return {
      ...chart,
      data: [],
    };
  }

  const labelKey = chart.config?.xAxis || "label";
  const valueKey = Array.isArray(chart.config?.yAxis)
    ? chart.config.yAxis[0]
    : chart.config?.yAxis || chart.config?.valueKey || "value";

  const data = labels.map((label, index) => ({
    [labelKey]: label,
    [valueKey]: values[index],
  }));

  return {
    ...chart,
    data,
    config: {
      ...chart.config,
      xAxis: labelKey,
      yAxis: valueKey,
      legend: chart.config?.legend ?? false,
    },
  };
}
