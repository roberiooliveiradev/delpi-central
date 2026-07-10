import { ConfigurableSeriesChart } from "./ConfigurableSeriesChart";
import { resolveChartDisplayOptions } from "./comunicadoChartOptions";
import type { ComunicadoChartOptions } from "./comunicadoChartOptions";
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

export function TvDataLineChartWidget({
  resolved,
  chartOptions,
}: {
  resolved: ComunicadoDataResolved;
  chartOptions?: ComunicadoChartOptions;
}) {
  const points = (resolved.chart?.points ?? []).map((point) => ({
    label: point.label != null ? String(point.label) : undefined,
    value: point.value == null ? null : Number(point.value),
  }));
  return (
    <ConfigurableSeriesChart
      chartType="line"
      points={points}
      options={resolveChartDisplayOptions(chartOptions, resolved)}
    />
  );
}

export function TvDataBarChartWidget({
  resolved,
  chartOptions,
}: {
  resolved: ComunicadoDataResolved;
  chartOptions?: ComunicadoChartOptions;
}) {
  const points = (resolved.chart?.points ?? []).map((point) => ({
    label: point.label != null ? String(point.label) : undefined,
    value: point.value == null ? null : Number(point.value),
  }));
  return (
    <ConfigurableSeriesChart
      chartType="bar"
      points={points}
      options={resolveChartDisplayOptions(chartOptions, resolved)}
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
