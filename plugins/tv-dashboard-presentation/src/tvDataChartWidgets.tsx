import { ConfigurableSeriesChart } from "./ConfigurableSeriesChart";
import { resolveChartDisplayOptions } from "./comunicadoChartOptions";
import type { ComunicadoChartOptions } from "./comunicadoChartOptions";
import type { ComunicadoChartInteraction, ComunicadoChartPartsMap } from "./comunicadoChartParts";
import { pieInnerRadiusForChartType, toSeriesChartKind } from "./comunicadoChartView";
import type { ComunicadoChartType, ComunicadoDataResolved } from "./comunicadoTypes";
import { formatNumber } from "./nativeFormat";
import { resolveEffectiveChartGoal } from "./resolveEffectiveChartGoal";

export function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    return formatNumber(value);
  }
  return String(value);
}

type ChartWidgetProps = {
  resolved: ComunicadoDataResolved;
  chartOptions?: ComunicadoChartOptions;
  chartParts?: ComunicadoChartPartsMap | null;
  interaction?: ComunicadoChartInteraction | null;
  chartType?: ComunicadoChartType;
};

export function TvDataSeriesChartWidget({
  resolved,
  chartOptions,
  chartParts,
  interaction,
  chartType = "line",
}: ChartWidgetProps) {
  const kind = toSeriesChartKind(chartType) ?? "line";
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
      points: series.points.map((point) => ({
        label: point.label != null ? String(point.label) : undefined,
        value: point.value == null ? null : Number(point.value),
        size:
          point.size == null || point.size === ""
            ? null
            : Number.isFinite(Number(point.size))
              ? Number(point.size)
              : null,
      })),
    }));
  const points =
    seriesList.length > 0
      ? seriesList[0]!.points
      : (resolved.chart?.points ?? []).map((point) => ({
          label: point.label != null ? String(point.label) : undefined,
          value: point.value == null ? null : Number(point.value),
          size:
            point.size == null || point.size === ""
              ? null
              : Number.isFinite(Number(point.size))
                ? Number(point.size)
                : null,
        }));
  // Bubble: size é canal no ponto — nunca overlay de 2ª série na legenda.
  const multiSeriesList =
    chartType === "bubble" ? undefined : seriesList.length > 1 ? seriesList : undefined;
  const displayOptions = resolveChartDisplayOptions(chartOptions, resolved);
  const effectiveGoal = resolveEffectiveChartGoal({
    goalLineValue: displayOptions.goalLineValue,
    projectedGoal: resolved.chart?.projectedGoal,
  });
  const optionsWithGoal = { ...displayOptions, goalLineValue: effectiveGoal };
  return (
    <ConfigurableSeriesChart
      chartType={kind}
      points={points}
      seriesList={multiSeriesList}
      options={optionsWithGoal}
      chartParts={chartParts}
      interaction={interaction}
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
  const value = formatCellValue(resolved.kpi?.value);
  return (
    <div className="tdp-data-kpi">
      <span className="tdp-data-kpi__label">{label}</span>
      <strong className="tdp-data-kpi__value">{value}</strong>
    </div>
  );
}
