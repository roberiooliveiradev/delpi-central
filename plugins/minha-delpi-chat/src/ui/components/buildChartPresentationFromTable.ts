import type { ChatPresentation } from "../../data/api/chatTypes";
import { inferDefaultChartAxes, listCategoryColumns, listNumericColumns } from "./chartAxisSelection";

type TablePresentation = Extract<ChatPresentation, { type: "table" }>;
type ChartPresentation = Extract<ChatPresentation, { type: "chart" }>;

export function tableSupportsChart(table: TablePresentation): boolean {
  return buildChartPresentationFromTable(table) !== null;
}

/** Monta gráfico a partir das linhas da tabela quando o backend não enviou chartPresentation. */
export function buildChartPresentationFromTable(
  table: TablePresentation,
): ChartPresentation | null {
  const rows = (table.rows ?? []).filter(
    (row): row is Record<string, unknown> =>
      typeof row === "object" && row !== null,
  );

  if (rows.length < 2) {
    return null;
  }

  const numericColumns = listNumericColumns(rows);
  const categoryColumns = listCategoryColumns(rows, numericColumns);

  if (!numericColumns.length) {
    return null;
  }

  const slice = rows.slice(0, 24);
  const chartType =
    categoryColumns.length >= 1 && numericColumns.length >= 1 ? "bar" : "scatter";
  const axes = inferDefaultChartAxes(slice, chartType);
  const yAxis = [
    axes.yKey,
    ...numericColumns.filter((key) => key !== axes.yKey),
  ].slice(0, 3);

  return {
    type: "chart",
    title: table.title || "Gráfico",
    chartType,
    data: slice,
    config: {
      xAxis: axes.xKey,
      yAxis: yAxis,
      legend: yAxis.length > 1,
    },
  };
}
