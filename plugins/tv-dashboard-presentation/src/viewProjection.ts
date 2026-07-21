import type { DelpiKpiColorRule } from "@delpi/plugin-ui/index";

import type {
  ComunicadoDataKpiMetric,
  ComunicadoDataResolved,
  ComunicadoDataTableColumn,
} from "./comunicadoTypes";
import {
  applyMetricSelectionToResolved,
  normalizeSelectedValueFields,
  type MetricSelection,
} from "./resolveKpiMetrics";

export type ViewAggregation = "first" | "sum" | "avg" | "min" | "max" | "count";

export const VIEW_AGGREGATION_OPTIONS: Array<{ value: ViewAggregation; label: string }> = [
  { value: "first", label: "Primeiro valor" },
  { value: "sum", label: "Soma" },
  { value: "avg", label: "Média" },
  { value: "min", label: "Mínimo" },
  { value: "max", label: "Máximo" },
  { value: "count", label: "Contagem de linhas" },
];

export type KpiMetricProjection = {
  field: string;
  aggregation?: ViewAggregation;
  label?: string;
  format?: "number" | "percent" | "compact" | "raw";
  colorRules?: DelpiKpiColorRule[];
  visible?: boolean;
};

export type KpiViewProjection = {
  metrics?: KpiMetricProjection[];
};

export type ChartSeriesProjection = {
  field: string;
  aggregation?: ViewAggregation;
  label?: string;
  color?: string;
  /** Eixo Y: primário (esquerda) ou secundário (direita). */
  plotOn?: "primary" | "secondary";
};

export type ChartViewProjection = {
  categoryField?: string;
  series?: ChartSeriesProjection[];
};

export type TableColumnProjection = {
  key: string;
  label?: string;
  visible: boolean;
  /** Largura relativa da coluna (% do total da tabela). */
  widthPct?: number;
};

export type TableViewProjection = {
  columns?: TableColumnProjection[];
};

export type ViewProjectionSelection = MetricSelection & {
  kpiProjection?: KpiViewProjection | null;
  chartProjection?: ChartViewProjection | null;
  tableProjection?: TableViewProjection | null;
};

function asFiniteNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value.replace(",", "."));
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

/** Agrega valores numéricos de uma coluna (ou lista escalar). */
export function aggregateValues(
  values: unknown[],
  aggregation: ViewAggregation = "first",
): number | null {
  if (aggregation === "count") return values.length;

  const nums = values.map(asFiniteNumber).filter((item): item is number => item != null);
  if (nums.length === 0) {
    if (aggregation === "first" && values.length > 0) {
      const first = asFiniteNumber(values[0]);
      return first;
    }
    return null;
  }

  switch (aggregation) {
    case "sum":
      return nums.reduce((acc, item) => acc + item, 0);
    case "avg":
      return nums.reduce((acc, item) => acc + item, 0) / nums.length;
    case "min":
      return Math.min(...nums);
    case "max":
      return Math.max(...nums);
    case "first":
    default:
      return nums[0] ?? null;
  }
}

export function columnValuesFromRows(
  rows: Array<Record<string, unknown>>,
  field: string,
): unknown[] {
  return rows.map((row) => row[field]);
}

/** Migra selectedValueFields legado → kpiProjection.metrics. */
export function kpiProjectionFromSelectedFields(
  selectedValueFields?: string[] | null,
  valueField?: string | null,
): KpiViewProjection | undefined {
  const fields =
    normalizeSelectedValueFields(selectedValueFields) ??
    (valueField?.trim() ? [valueField.trim()] : undefined);
  if (!fields?.length) return undefined;
  return {
    metrics: fields.map((field) => ({ field, visible: true, aggregation: "first" as const })),
  };
}

/** Migra selectedValueFields → chartProjection.series. */
export function chartProjectionFromSelectedFields(
  selectedValueFields?: string[] | null,
  valueField?: string | null,
): ChartViewProjection | undefined {
  const fields =
    normalizeSelectedValueFields(selectedValueFields) ??
    (valueField?.trim() ? [valueField.trim()] : undefined);
  if (!fields?.length) return undefined;
  return {
    series: fields.map((field) => ({ field, aggregation: "first" as const })),
  };
}

/** Migra selectedValueFields → tableProjection.columns (keys = fields). */
export function tableProjectionFromSelectedFields(
  selectedValueFields?: string[] | null,
  valueField?: string | null,
): TableViewProjection | undefined {
  const fields =
    normalizeSelectedValueFields(selectedValueFields) ??
    (valueField?.trim() ? [valueField.trim()] : undefined);
  if (!fields?.length) return undefined;
  return {
    columns: fields.map((key) => ({ key, visible: true })),
  };
}

export function normalizeKpiProjection(raw: unknown): KpiViewProjection | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const metricsRaw = (raw as KpiViewProjection).metrics;
  if (!Array.isArray(metricsRaw)) return undefined;
  const metrics = metricsRaw
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const field = String((item as KpiMetricProjection).field ?? "").trim();
      if (!field) return null;
      const metric: KpiMetricProjection = { field };
      const agg = (item as KpiMetricProjection).aggregation;
      if (agg) metric.aggregation = agg;
      if (typeof (item as KpiMetricProjection).label === "string") {
        metric.label = (item as KpiMetricProjection).label;
      }
      if ((item as KpiMetricProjection).format) {
        metric.format = (item as KpiMetricProjection).format;
      }
      if (Array.isArray((item as KpiMetricProjection).colorRules)) {
        metric.colorRules = [...((item as KpiMetricProjection).colorRules ?? [])];
      }
      if (typeof (item as KpiMetricProjection).visible === "boolean") {
        metric.visible = (item as KpiMetricProjection).visible;
      }
      return metric;
    })
    .filter((item): item is KpiMetricProjection => item != null);
  return metrics.length > 0 ? { metrics } : undefined;
}

export function normalizeChartProjection(raw: unknown): ChartViewProjection | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const next: ChartViewProjection = {};
  const category = String((raw as ChartViewProjection).categoryField ?? "").trim();
  if (category) next.categoryField = category;
  const seriesRaw = (raw as ChartViewProjection).series;
  if (Array.isArray(seriesRaw)) {
    const series = seriesRaw
      .map((item) => {
        if (!item || typeof item !== "object") return null;
        const field = String((item as ChartSeriesProjection).field ?? "").trim();
        if (!field) return null;
        const entry: ChartSeriesProjection = { field };
        if ((item as ChartSeriesProjection).aggregation) {
          entry.aggregation = (item as ChartSeriesProjection).aggregation;
        }
        if (typeof (item as ChartSeriesProjection).label === "string") {
          entry.label = (item as ChartSeriesProjection).label;
        }
        if (typeof (item as ChartSeriesProjection).color === "string") {
          entry.color = (item as ChartSeriesProjection).color;
        }
        const plotOn = (item as ChartSeriesProjection).plotOn;
        if (plotOn === "primary" || plotOn === "secondary") {
          entry.plotOn = plotOn;
        }
        return entry;
      })
      .filter((item): item is ChartSeriesProjection => item != null);
    if (series.length > 0) next.series = series;
  }
  return next.categoryField || next.series ? next : undefined;
}

export function normalizeTableProjection(raw: unknown): TableViewProjection | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const columnsRaw = (raw as TableViewProjection).columns;
  if (!Array.isArray(columnsRaw)) return undefined;
  const columns = columnsRaw
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const key = String((item as TableColumnProjection).key ?? "").trim();
      if (!key) return null;
      const col: TableColumnProjection = {
        key,
        visible: (item as TableColumnProjection).visible !== false,
      };
      if (typeof (item as TableColumnProjection).label === "string") {
        col.label = (item as TableColumnProjection).label;
      }
      const widthPct = asFiniteNumber((item as TableColumnProjection).widthPct);
      if (widthPct != null && widthPct > 0) {
        col.widthPct = Math.max(1, Math.min(100, widthPct));
      }
      return col;
    })
    .filter((item): item is TableColumnProjection => item != null);
  return columns.length > 0 ? { columns } : undefined;
}

function resolveKpiMetricsWithProjection(
  resolved: ComunicadoDataResolved,
  projection: KpiViewProjection | undefined,
  fallbackSelection: MetricSelection,
): ComunicadoDataKpiMetric[] {
  const rows = resolved.table?.rows ?? [];
  const existing = resolved.kpiMetrics ?? [];
  const byField = new Map(existing.map((metric) => [metric.field, metric]));

  const projected = projection?.metrics?.filter((metric) => metric.visible !== false);
  if (projected && projected.length > 0) {
    return projected.map((metric) => {
      const base = byField.get(metric.field);
      const rowValues =
        rows.length > 0
          ? columnValuesFromRows(rows, metric.field).filter((value) => value != null && value !== "")
          : [];
      const fromRows =
        rowValues.length > 0
          ? aggregateValues(rowValues, metric.aggregation ?? "first")
          : null;
      const value =
        fromRows != null
          ? fromRows
          : metric.aggregation && metric.aggregation !== "first" && base?.value != null
            ? aggregateValues([base.value], metric.aggregation)
            : base?.value;
      return {
        field: metric.field,
        label: metric.label?.trim() || base?.label || metric.field,
        value: value ?? base?.value,
      };
    });
  }

  const selected = applyMetricSelectionToResolved(resolved, fallbackSelection);
  return selected?.kpiMetrics ?? existing;
}

function applyTableProjection(
  resolved: ComunicadoDataResolved,
  projection: TableViewProjection | undefined,
): ComunicadoDataResolved {
  const rows = resolved.table?.rows ?? [];
  const columns = resolved.table?.columns ?? [];
  if (!projection?.columns?.length || rows.length === 0) {
    return resolved;
  }

  const visible = projection.columns.filter((col) => col.visible !== false);
  if (visible.length === 0) {
    return {
      ...resolved,
      table: { rows: [], columns: [] },
    };
  }

  const labelByKey = new Map(
    columns.map((col) => [col.key, col.label] as const),
  );
  const nextColumns: ComunicadoDataTableColumn[] = visible.map((col) => ({
    key: col.key,
    label: col.label?.trim() || labelByKey.get(col.key) || col.key,
  }));
  const keys = new Set(nextColumns.map((col) => col.key));
  const nextRows = rows.map((row) => {
    const next: Record<string, unknown> = {};
    for (const key of keys) {
      if (key in row) next[key] = row[key];
    }
    return next;
  });

  return {
    ...resolved,
    table: { rows: nextRows, columns: nextColumns },
  };
}

function buildSeriesFromTable(
  rows: Array<Record<string, unknown>>,
  categoryField: string | undefined,
  seriesDefs: ChartSeriesProjection[],
): NonNullable<ComunicadoDataResolved["chart"]> {
  const categories = rows.map((row, index) => {
    if (categoryField && row[categoryField] != null) return String(row[categoryField]);
    return String(index + 1);
  });

  if (seriesDefs.length <= 1) {
    const def = seriesDefs[0];
    const field = def?.field;
    const points = rows.map((row, index) => ({
      label: categories[index],
      value: field
        ? aggregateValues([row[field]], def?.aggregation ?? "first")
        : null,
    }));
    return {
      points,
      chartType: "line",
      series: def
        ? [
            {
              name: def.label?.trim() || def.field,
              field: def.field,
              points,
              color: def.color,
              plotOn: def.plotOn,
            },
          ]
        : undefined,
    };
  }

  const series = seriesDefs.map((def) => ({
    name: def.label?.trim() || def.field,
    field: def.field,
    color: def.color,
    plotOn: def.plotOn,
    points: rows.map((row, index) => ({
      label: categories[index],
      value: aggregateValues([row[def.field]], def.aggregation ?? "first"),
    })),
  }));

  return {
    points: series[0]?.points ?? [],
    chartType: "line",
    series,
  };
}

function applyChartProjection(
  resolved: ComunicadoDataResolved,
  projection: ChartViewProjection | undefined,
  fallbackSelection: MetricSelection,
): ComunicadoDataResolved {
  const rows = resolved.table?.rows ?? [];
  const seriesDefs = projection?.series ?? [];

  if (seriesDefs.length > 0 && rows.length > 0) {
    const chart = buildSeriesFromTable(rows, projection?.categoryField, seriesDefs);
    return { ...resolved, chart };
  }

  if (seriesDefs.length > 1 && (resolved.kpiMetrics?.length ?? 0) > 0) {
    const byField = new Map((resolved.kpiMetrics ?? []).map((metric) => [metric.field, metric]));
    const series = seriesDefs
      .map((def) => {
        const metric = byField.get(def.field);
        if (!metric) return null;
        return {
          name: def.label?.trim() || metric.label || def.field,
          field: def.field,
          color: def.color,
          plotOn: def.plotOn,
          points: [{ label: metric.label, value: asFiniteNumber(metric.value) }],
        };
      })
      .filter((item): item is NonNullable<typeof item> => item != null);
    if (series.length > 0) {
      return {
        ...resolved,
        chart: {
          points: series.flatMap((item) => item.points),
          chartType: "bar",
          series,
        },
      };
    }
  }

  if (seriesDefs.length === 1 || (!projection && fallbackSelection)) {
    const selection: MetricSelection =
      seriesDefs.length > 0
        ? { selectedValueFields: seriesDefs.map((item) => item.field) }
        : fallbackSelection;
    return applyMetricSelectionToResolved(resolved, selection) ?? resolved;
  }

  return resolved;
}

/**
 * Aplica projeção do visual sobre o resolved compartilhado da fonte.
 * Sem projeção, preserva `applyMetricSelectionToResolved` (legado).
 */
export function applyViewProjection(
  resolved: ComunicadoDataResolved | undefined,
  selection: ViewProjectionSelection,
): ComunicadoDataResolved | undefined {
  if (!resolved) return resolved;

  // Servidor já projetou (enrichment) — só filtra métricas visíveis se necessário.
  if (resolved.serverProjectionApplied) {
    if (selection.kpiProjection?.metrics?.length) {
      const visible = new Set(
        selection.kpiProjection.metrics
          .filter((metric) => metric.visible !== false)
          .map((metric) => metric.field),
      );
      const metrics = (resolved.kpiMetrics ?? []).filter((metric) => visible.has(metric.field));
      if (metrics.length > 0) {
        return {
          ...resolved,
          kpiMetrics: metrics,
          kpi: { value: metrics[0]?.value, label: metrics[0]?.label },
        };
      }
    }
    return resolved;
  }

  const fallback: MetricSelection = {
    selectedValueFields: selection.selectedValueFields,
    valueField: selection.valueField,
  };

  let next = { ...resolved };

  if (selection.kpiProjection?.metrics?.length) {
    const metrics = resolveKpiMetricsWithProjection(next, selection.kpiProjection, fallback);
    const primary = metrics[0];
    next = {
      ...next,
      kpiMetrics: metrics,
      kpi: primary
        ? { value: primary.value, label: primary.label }
        : next.kpi,
    };
  } else if (fallback.selectedValueFields?.length || fallback.valueField) {
    next = applyMetricSelectionToResolved(next, fallback) ?? next;
  }

  if (selection.tableProjection?.columns?.length) {
    next = applyTableProjection(next, selection.tableProjection);
  }

  if (selection.chartProjection?.series?.length || selection.chartProjection?.categoryField) {
    next = applyChartProjection(next, selection.chartProjection, fallback);
  }

  return next;
}

/** Descobre campos disponíveis no resolved (runtime + catálogo). */
export function discoverResolvedFieldOptions(
  resolved: ComunicadoDataResolved | undefined,
  catalogFields?: Array<{ field: string; label: string }>,
): Array<{ field: string; label: string }> {
  const out = new Map<string, string>();
  for (const item of catalogFields ?? []) {
    const field = item.field.trim();
    if (field) out.set(field, item.label.trim() || field);
  }
  for (const metric of resolved?.kpiMetrics ?? []) {
    if (metric.field) out.set(metric.field, metric.label || metric.field);
  }
  for (const col of resolved?.table?.columns ?? []) {
    if (col.key) out.set(col.key, col.label || col.key);
  }
  const firstRow = resolved?.table?.rows?.[0];
  if (firstRow && typeof firstRow === "object") {
    for (const key of Object.keys(firstRow)) {
      if (!out.has(key)) out.set(key, key);
    }
  }
  return [...out.entries()].map(([field, label]) => ({ field, label }));
}

/** Sugere projeções iniciais ao conectar uma fonte (sem sobrescrever config existente). */
export function suggestDefaultProjections(
  resolved: ComunicadoDataResolved | undefined,
  fieldTypes?: Record<string, "number" | "string" | "date"> | null,
): {
  kpiProjection?: KpiViewProjection;
  chartProjection?: ChartViewProjection;
  tableProjection?: TableViewProjection;
} {
  if (!resolved) return {};
  const fields = discoverResolvedFieldOptions(resolved);
  const typeOf = (field: string): "number" | "string" | "date" | undefined =>
    fieldTypes?.[field];

  const numericFields = fields.filter((item) => {
    const declared = typeOf(item.field);
    const rows = resolved.table?.rows ?? [];
    const hasFiniteSample = () =>
      rows.some((row) => {
        const sample = row[item.field];
        return sample != null && sample !== "" && asFiniteNumber(sample) != null;
      });
    if (declared === "string" || declared === "date") return false;
    if (declared === "number") {
      // Tipo declarado no catálogo não basta — campo fantasma (ex.: quantidade no OEE) quebra o default.
      if (rows.length === 0) {
        const metric = resolved.kpiMetrics?.find((entry) => entry.field === item.field);
        return Boolean(metric && metric.value != null && metric.value !== "");
      }
      return hasFiniteSample();
    }
    const metric = resolved.kpiMetrics?.find((entry) => entry.field === item.field);
    if (metric && metric.value != null && metric.value !== "") return true;
    return hasFiniteSample();
  });

  const categoryCandidate =
    fields.find((item) => {
      const declared = typeOf(item.field);
      if (declared === "date" || declared === "string") return true;
      if (declared === "number") return false;
      const sample = resolved.table?.rows?.[0]?.[item.field];
      return typeof sample === "string" && asFiniteNumber(sample) == null;
    })?.field ?? fields[0]?.field;

  const kpiProjection: KpiViewProjection | undefined =
    numericFields.length > 0
      ? {
          metrics: numericFields.slice(0, 12).map((item) => ({
            field: item.field,
            label: item.label,
            visible: true,
            aggregation: "first",
          })),
        }
      : undefined;

  const chartProjection: ChartViewProjection | undefined =
    numericFields.length > 0
      ? {
          categoryField: categoryCandidate,
          series: numericFields.slice(0, 6).map((item) => ({
            field: item.field,
            label: item.label,
          })),
        }
      : undefined;

  const tableProjection: TableViewProjection | undefined =
    fields.length > 0
      ? {
          columns: fields.map((item) => ({
            key: item.field,
            label: item.label,
            visible: true,
          })),
        }
      : undefined;

  return { kpiProjection, chartProjection, tableProjection };
}
