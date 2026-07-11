import { ConfigurableSeriesChart } from "./ConfigurableSeriesChart";
import { resolveChartDisplayOptions } from "./comunicadoChartOptions";
import type { ComunicadoChartOptions } from "./comunicadoChartOptions";
import type { ComunicadoChartInteraction, ComunicadoChartPartsMap } from "./comunicadoChartParts";
import type { ComunicadoDataResolved } from "./comunicadoTypes";
import { formatNumber, formatPct } from "./nativeFormat";

export function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    if (Math.abs(value) <= 100 && !Number.isInteger(value)) return formatPct(value);
    return formatNumber(value);
  }
  return String(value);
}

type ChartWidgetProps = {
  resolved: ComunicadoDataResolved;
  chartOptions?: ComunicadoChartOptions;
  chartParts?: ComunicadoChartPartsMap | null;
  interaction?: ComunicadoChartInteraction | null;
};

export function TvDataLineChartWidget({
  resolved,
  chartOptions,
  chartParts,
  interaction,
}: ChartWidgetProps) {
  const points = (resolved.chart?.points ?? []).map((point) => ({
    label: point.label != null ? String(point.label) : undefined,
    value: point.value == null ? null : Number(point.value),
  }));
  return (
    <ConfigurableSeriesChart
      chartType="line"
      points={points}
      options={resolveChartDisplayOptions(chartOptions, resolved)}
      chartParts={chartParts}
      interaction={interaction}
    />
  );
}

export function TvDataBarChartWidget({
  resolved,
  chartOptions,
  chartParts,
  interaction,
}: ChartWidgetProps) {
  const points = (resolved.chart?.points ?? []).map((point) => ({
    label: point.label != null ? String(point.label) : undefined,
    value: point.value == null ? null : Number(point.value),
  }));
  return (
    <ConfigurableSeriesChart
      chartType="bar"
      points={points}
      options={resolveChartDisplayOptions(chartOptions, resolved)}
      chartParts={chartParts}
      interaction={interaction}
    />
  );
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
