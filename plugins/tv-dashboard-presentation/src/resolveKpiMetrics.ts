import type {
  ComunicadoDataKpiMetric,
  ComunicadoDataResolved,
} from "./comunicadoTypes";

export type MetricSelection = {
  selectedValueFields?: string[] | null;
  valueField?: string | null;
};

/** Normaliza seleção: lista limpa ou undefined (= todas). */
export function normalizeSelectedValueFields(
  fields: unknown,
): string[] | undefined {
  if (!Array.isArray(fields)) return undefined;
  const cleaned = fields
    .map((item) => String(item ?? "").trim())
    .filter(Boolean);
  return cleaned.length > 0 ? cleaned : undefined;
}

export function resolveSelectedMetricFields(selection: MetricSelection): string[] | undefined {
  const multi = normalizeSelectedValueFields(selection.selectedValueFields);
  if (multi) return multi;
  const single = selection.valueField?.trim();
  return single ? [single] : undefined;
}

/** Filtra métricas do resolved conforme seleção do visual/fonte. */
export function filterKpiMetrics(
  metrics: ComunicadoDataKpiMetric[] | undefined,
  selection: MetricSelection,
): ComunicadoDataKpiMetric[] {
  const all = Array.isArray(metrics) ? metrics : [];
  const wanted = resolveSelectedMetricFields(selection);
  if (!wanted || wanted.length === 0) return all;
  const order = new Map(wanted.map((field, index) => [field, index]));
  return all
    .filter((metric) => order.has(metric.field))
    .sort((a, b) => (order.get(a.field) ?? 999) - (order.get(b.field) ?? 999));
}

/**
 * Aplica seleção de métricas ao resolved para render (KPI grade / chart / table).
 * Mantém série temporal intacta quando há vários pontos com labels distintos de field keys.
 */
export function applyMetricSelectionToResolved(
  resolved: ComunicadoDataResolved | undefined,
  selection: MetricSelection,
): ComunicadoDataResolved | undefined {
  if (!resolved) return resolved;
  const metrics = filterKpiMetrics(resolved.kpiMetrics, selection);
  if (!resolved.kpiMetrics || resolved.kpiMetrics.length === 0) {
    return resolved;
  }

  const primary = metrics[0];
  const next: ComunicadoDataResolved = {
    ...resolved,
    kpiMetrics: metrics,
    kpi: primary
      ? { value: primary.value, label: primary.label }
      : resolved.kpi,
  };

  const chartPoints = resolved.chart?.points ?? [];
  const looksLikeMetricBars =
    chartPoints.length > 0 &&
    chartPoints.length <= (resolved.kpiMetrics?.length ?? 0) + 2 &&
    chartPoints.every((point) => {
      const label = point.label != null ? String(point.label) : "";
      return (
        !label ||
        (resolved.kpiMetrics ?? []).some(
          (metric) => metric.label === label || metric.field === label,
        )
      );
    });

  if (looksLikeMetricBars || chartPoints.length <= 1) {
    next.chart = {
      points: metrics.map((metric) => ({
        label: metric.label,
        value: metric.value,
      })),
      chartType: metrics.length > 1 ? "bar" : resolved.chart?.chartType ?? "line",
    };
  }

  const tableRows = resolved.table?.rows ?? [];
  const looksLikeMetricTable =
    tableRows.length > 0 &&
    tableRows.every(
      (row) =>
        typeof row === "object" &&
        row != null &&
        ("metric" in row || "field" in row) &&
        "value" in row,
    );

  if (looksLikeMetricTable || tableRows.length <= 1) {
    next.table = {
      rows: metrics.map((metric) => ({
        metric: metric.label,
        field: metric.field,
        value: metric.value,
      })),
      columns: [
        { key: "metric", label: "Indicador" },
        { key: "value", label: "Valor" },
      ],
    };
  }

  return next;
}
