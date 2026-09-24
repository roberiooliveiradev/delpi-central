import { ConfigurableSeriesChart } from "./ConfigurableSeriesChart";
import { resolveChartDisplayOptions } from "./comunicadoChartOptions";
import type { ComunicadoChartOptions } from "./comunicadoChartOptions";
import type { ComunicadoChartInteraction, ComunicadoChartPartsMap } from "./comunicadoChartParts";
import { pieInnerRadiusForChartType, toSeriesChartKind } from "./comunicadoChartView";
import type { ComunicadoChartType, ComunicadoDataResolved } from "./comunicadoTypes";
import { resolveEffectiveChartGoal } from "./resolveEffectiveChartGoal";

export function formatCellValue(value: unknown): string {
  // Paint-only residual: sem display* do servidor → unresolved (não formatDisplayValue).
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value.trim() ? value : "—";
  if (typeof value === "number" && Number.isFinite(value)) return "—";
  return "—";
}

type ChartWidgetProps = {
  resolved: ComunicadoDataResolved;
  chartOptions?: ComunicadoChartOptions;
  chartParts?: ComunicadoChartPartsMap | null;
  interaction?: ComunicadoChartInteraction | null;
  chartType?: ComunicadoChartType;
  emptyMessage?: string;
};

export function TvDataSeriesChartWidget({
  resolved,
  chartOptions,
  chartParts,
  interaction,
  chartType = "line",
  emptyMessage = "Sem dados",
}: ChartWidgetProps) {
  const kind = toSeriesChartKind(chartType) ?? "line";
  const mapPoint = (point: {
    label?: unknown;
    value?: unknown;
    size?: unknown;
    displayLabel?: string;
    displayValue?: string;
  }) => {
    const hasDisplayLabel = typeof point.displayLabel === "string";
    return {
      label: hasDisplayLabel
        ? point.displayLabel
        : point.label != null
          ? String(point.label)
          : undefined,
      value: point.value == null ? null : Number(point.value),
      size:
        point.size == null || point.size === ""
          ? null
          : Number.isFinite(Number(point.size))
            ? Number(point.size)
            : null,
      ...(typeof point.displayValue === "string"
        ? { displayValue: point.displayValue }
        : {}),
    };
  };
  const seriesList = (resolved.chart?.series ?? [])
    .filter((series) =>
      Array.isArray(series.points) &&
      series.points.some((point) => {
        if (point.value == null || point.value === "") return false;
        return Number.isFinite(Number(point.value));
      }),
    )
    .map((series) => ({
      name: series.name,
      color: series.color,
      plotOn: series.plotOn,
      points: series.points.map(mapPoint),
    }));
  const points =
    seriesList.length > 0
      ? seriesList[0]!.points
      : (resolved.chart?.points ?? []).map(mapPoint);
  const hasPlotData =
    points.some((point) => point.value != null && Number.isFinite(Number(point.value))) ||
    Boolean(
      seriesList.some((series) =>
        series.points.some(
          (point) => point.value != null && Number.isFinite(Number(point.value)),
        ),
      ),
    );
  const hasServerCategoryDisplay = (resolved.chart?.points ?? [])
    .concat((resolved.chart?.series ?? []).flatMap((s) => s.points ?? []))
    .some((point) => typeof point.displayLabel === "string");
  // Bubble: size é canal no ponto — nunca overlay de 2ª série na legenda.
  const multiSeriesList =
    chartType === "bubble" ? undefined : seriesList.length > 1 ? seriesList : undefined;
  // Sem série plotável: não herdar kpi.label (ex.: buckets_count) como título do gráfico.
  const displayOptions = resolveChartDisplayOptions(
    chartOptions,
    hasPlotData ? resolved : { label: resolved.label },
  );
  const paintOptions = hasServerCategoryDisplay
    ? {
        ...displayOptions,
        categoryLabelFormat: "raw" as const,
        displayCategoryFormat: undefined,
      }
    : displayOptions;
  const effectiveGoal = resolveEffectiveChartGoal({
    goalLineValue: paintOptions.goalLineValue,
    projectedGoal: resolved.chart?.projectedGoal,
  });
  const optionsWithGoal = {
    ...paintOptions,
    goalLineValue: effectiveGoal,
    ...(Array.isArray(resolved.chart?.yAxisTicks) && resolved.chart.yAxisTicks.length >= 2
      ? { yAxisTicks: resolved.chart.yAxisTicks }
      : {}),
  };
  return (
    <ConfigurableSeriesChart
      chartType={kind}
      points={points}
      seriesList={multiSeriesList}
      options={optionsWithGoal}
      chartParts={chartParts}
      interaction={interaction}
      emptyMessage={emptyMessage}
      pieInnerRadiusRatio={pieInnerRadiusForChartType(chartType)}
    />
  );
}

/** @deprecated Use TvDataSeriesChartWidget. */
export function TvDataLineChartWidget(props: ChartWidgetProps) {
  return <TvDataSeriesChartWidget {...props} chartType={props.chartType ?? "line"} />;
}

/** @deprecated Use TvDataSeriesChartWidget. */
export function TvDataBarChartWidget(props: ChartWidgetProps) {
  return <TvDataSeriesChartWidget {...props} chartType={props.chartType ?? "bar"} />;
}

export function TvDataKpiWidget({ resolved }: { resolved: ComunicadoDataResolved }) {
  const label = resolved.kpi?.label ?? resolved.label ?? "Dados";
  const value =
    typeof resolved.kpi?.displayValue === "string"
      ? resolved.kpi.displayValue
      : formatCellValue(resolved.kpi?.value);
  return (
    <div className="tdp-data-kpi">
      <span className="tdp-data-kpi__label">{label}</span>
      <strong className="tdp-data-kpi__value">{value}</strong>
    </div>
  );
}
