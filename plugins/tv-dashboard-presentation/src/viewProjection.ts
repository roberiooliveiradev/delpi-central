import type { DelpiKpiColorRule } from "@delpi/plugin-ui/index";

import {
  resolveChartDataPolicy,
  type ChartDataPolicy,
} from "./chartDataPolicy";
import type {
  ComunicadoChartType,
  ComunicadoDataKpiMetric,
  ComunicadoDataResolved,
  ComunicadoDataTableColumn,
} from "./comunicadoTypes";
import {
  aggregateProjectionValues,
  columnValuesFromRows,
  parseProjectionNumber,
  type ViewAggregation,
} from "./fieldValueProjection";
import { resolveFieldDisplayLabel } from "./fieldLabelRegistry";
import {
  applyMetricSelectionToResolved,
  normalizeSelectedValueFields,
  type MetricSelection,
} from "./resolveKpiMetrics";

export type { ViewAggregation } from "./fieldValueProjection";
export { VIEW_AGGREGATION_OPTIONS, columnValuesFromRows } from "./fieldValueProjection";

export type KpiMetricProjection = {
  field: string;
  aggregation?: ViewAggregation;
  label?: string;
  format?: "number" | "percent" | "compact" | "raw" | "currency";
  colorRules?: DelpiKpiColorRule[];
  visible?: boolean;
  /** Meta por métrica (multi-KPI). */
  target?: number;
  comparisonMode?: "none" | "target" | "previous";
  higherIsBetter?: boolean;
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
  /** Tipo do visual — define policy de group-by / wells (Playbook chart-data-policies). */
  chartType?: ComunicadoChartType | null;
};

function asFiniteNumber(value: unknown): number | null {
  return parseProjectionNumber(value);
}

/** Agrega valores numéricos de uma coluna (ou lista escalar). Delegado canônico: fieldValueProjection. */
export function aggregateValues(
  values: unknown[],
  aggregation: ViewAggregation = "first",
): number | null {
  return aggregateProjectionValues(values, aggregation);
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
        label: resolveFieldDisplayLabel({
          field: metric.field,
          projectionLabel: metric.label,
          resolvedLabel: base?.label,
        }),
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
    label: resolveFieldDisplayLabel({
      field: col.key,
      projectionLabel: col.label,
      resolvedLabel: labelByKey.get(col.key),
    }),
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
  policy: ChartDataPolicy,
): NonNullable<ComunicadoDataResolved["chart"]> {
  const chartType = policy.chartType;

  if (policy.rowMode === "groupByCategory" && categoryField) {
    return buildGroupedSeriesFromTable(rows, categoryField, seriesDefs, policy);
  }

  // scatter/bubble: categoryField guarda a medida X (rótulo numérico).
  const categories = rows.map((row, index) => {
    if (categoryField && row[categoryField] != null) return String(row[categoryField]);
    return String(index + 1);
  });

  if (seriesDefs.length <= 1) {
    const def = seriesDefs[0];
    const field = def?.field;
    const points = rows.map((row, index) => ({
      label: categories[index],
      value: resolveSeriesPointValue(row, field, def?.aggregation, policy),
    }));
    return {
      points,
      chartType,
      series: def
        ? [
            {
              name: resolveFieldDisplayLabel({
                field: def.field,
                projectionLabel: def.label,
              }),
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
    name: resolveFieldDisplayLabel({
      field: def.field,
      projectionLabel: def.label,
    }),
    field: def.field,
    color: def.color,
    plotOn: def.plotOn,
    points: rows.map((row, index) => ({
      label: categories[index],
      value: resolveSeriesPointValue(row, def.field, def.aggregation, policy),
    })),
  }));

  return {
    points: series[0]?.points ?? [],
    chartType,
    series,
  };
}

function resolveSeriesPointValue(
  row: Record<string, unknown>,
  field: string | undefined,
  aggregation: ViewAggregation | undefined,
  policy: ChartDataPolicy,
): number | null {
  if (!field) {
    return policy.defaultAggregation === "count" ? 1 : null;
  }
  const agg = aggregation ?? policy.defaultAggregation;
  if (agg === "count") {
    return 1;
  }
  const parsed = aggregateValues([row[field]], agg);
  if (parsed != null) return parsed;
  // Distribuição part-to-whole: medida ausente → conta a linha.
  if (policy.defaultAggregation === "count") return 1;
  return null;
}

function buildGroupedSeriesFromTable(
  rows: Array<Record<string, unknown>>,
  categoryField: string,
  seriesDefs: ChartSeriesProjection[],
  policy: ChartDataPolicy,
): NonNullable<ComunicadoDataResolved["chart"]> {
  const groups = new Map<string, Array<Record<string, unknown>>>();
  for (const row of rows) {
    const raw = row[categoryField];
    const key = raw == null || raw === "" ? "(vazio)" : String(raw);
    const bucket = groups.get(key);
    if (bucket) bucket.push(row);
    else groups.set(key, [row]);
  }

  let categoryKeys = [...groups.keys()];
  if (policy.maxCategories != null && categoryKeys.length > policy.maxCategories) {
    // Mantém as maiores categorias por contagem; resto → Outros.
    const ranked = categoryKeys
      .map((key) => ({ key, n: groups.get(key)?.length ?? 0 }))
      .sort((a, b) => b.n - a.n);
    const keep = new Set(ranked.slice(0, policy.maxCategories - 1).map((item) => item.key));
    const others: Array<Record<string, unknown>> = [];
    for (const key of categoryKeys) {
      if (keep.has(key)) continue;
      others.push(...(groups.get(key) ?? []));
      groups.delete(key);
    }
    if (others.length > 0) groups.set("Outros", others);
    categoryKeys = [...groups.keys()];
  }

  // Funil: ordenar por valor da 1ª série (desc).
  if (policy.chartType === "funnel" && seriesDefs[0]) {
    const def = seriesDefs[0];
    categoryKeys.sort((a, b) => {
      const va = aggregateGroupRows(groups.get(a) ?? [], def.field, def.aggregation, policy) ?? 0;
      const vb = aggregateGroupRows(groups.get(b) ?? [], def.field, def.aggregation, policy) ?? 0;
      return vb - va;
    });
  }

  const effectiveDefs =
    seriesDefs.length > 0
      ? seriesDefs
      : [{ field: categoryField, aggregation: "count" as const, label: "Contagem" }];

  if (effectiveDefs.length <= 1) {
    const def = effectiveDefs[0]!;
    const points = categoryKeys.map((key) => ({
      label: key,
      value: aggregateGroupRows(groups.get(key) ?? [], def.field, def.aggregation, policy),
    }));
    return {
      points,
      chartType: policy.chartType,
      series: [
        {
          name: resolveFieldDisplayLabel({
            field: def.field,
            projectionLabel: def.label,
          }),
          field: def.field,
          points,
          color: def.color,
          plotOn: def.plotOn,
        },
      ],
    };
  }

  const series = effectiveDefs.map((def) => ({
    name: resolveFieldDisplayLabel({
      field: def.field,
      projectionLabel: def.label,
    }),
    field: def.field,
    color: def.color,
    plotOn: def.plotOn,
    points: categoryKeys.map((key) => ({
      label: key,
      value: aggregateGroupRows(groups.get(key) ?? [], def.field, def.aggregation, policy),
    })),
  }));

  return {
    points: series[0]?.points ?? [],
    chartType: policy.chartType,
    series,
  };
}

function aggregateGroupRows(
  groupRows: Array<Record<string, unknown>>,
  field: string,
  aggregation: ViewAggregation | undefined,
  policy: ChartDataPolicy,
): number | null {
  const agg = aggregation ?? policy.defaultAggregation;
  if (agg === "count") return groupRows.length;
  const values = groupRows.map((row) => row[field]);
  const hasFinite = values.some((value) => asFiniteNumber(value) != null);
  if (!hasFinite) {
    // Part-to-whole / comparação: medida fantasma ou ausente → conta linhas do grupo.
    if (
      policy.rowMode === "groupByCategory" &&
      (policy.defaultAggregation === "count" ||
        policy.family === "distribution" ||
        policy.family === "comparison")
    ) {
      return groupRows.length;
    }
    return null;
  }
  return aggregateValues(values, agg);
}

function applyChartProjection(
  resolved: ComunicadoDataResolved,
  projection: ChartViewProjection | undefined,
  fallbackSelection: MetricSelection,
  chartType: ComunicadoChartType = "line",
): ComunicadoDataResolved {
  const rows = resolved.table?.rows ?? [];
  const seriesDefs = projection?.series ?? [];
  const policy = resolveChartDataPolicy(chartType);

  if (seriesDefs.length > 0 && rows.length > 0) {
    const chart = buildSeriesFromTable(
      rows,
      projection?.categoryField,
      seriesDefs,
      policy,
    );
    return { ...resolved, chart };
  }

  // Pizza/barra sem série explícita: só categoria → contagem por grupo.
  if (
    policy.rowMode === "groupByCategory" &&
    projection?.categoryField &&
    rows.length > 0 &&
    seriesDefs.length === 0
  ) {
    const chart = buildSeriesFromTable(
      rows,
      projection.categoryField,
      [{ field: projection.categoryField, aggregation: "count", label: "Contagem" }],
      policy,
    );
    return { ...resolved, chart };
  }

  if (seriesDefs.length > 1 && (resolved.kpiMetrics?.length ?? 0) > 0) {
    const byField = new Map((resolved.kpiMetrics ?? []).map((metric) => [metric.field, metric]));
    const series = seriesDefs
      .map((def) => {
        const metric = byField.get(def.field);
        if (!metric) return null;
        return {
          name: resolveFieldDisplayLabel({
            field: def.field,
            projectionLabel: def.label,
            resolvedLabel: metric.label,
          }),
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
          chartType: policy.chartType === "line" ? "bar" : policy.chartType,
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
    next = applyChartProjection(
      next,
      selection.chartProjection,
      fallback,
      selection.chartType ?? "line",
    );
  }

  return next;
}

/** Descobre campos disponíveis no resolved (runtime + catálogo). */
export function discoverResolvedFieldOptions(
  resolved: ComunicadoDataResolved | undefined,
  catalogFields?: Array<{ field: string; label: string }>,
  sourceFieldLabels?: Record<string, string> | null,
): Array<{ field: string; label: string }> {
  const out = new Map<string, string>();

  const put = (field: string, label: string, prefer = false) => {
    const key = field.trim();
    if (!key) return;
    const text = label.trim() || key;
    if (!prefer && out.has(key)) return;
    out.set(key, text);
  };

  const isCuratedLabel = (field: string, label: string) => {
    const text = label.trim();
    if (!text || text === field) return false;
    if (text === field.replace(/_/g, " ")) return false;
    return true;
  };

  // Runtime primeiro (kpiMetrics / colunas já rotulados pela API).
  if (resolved?.kpi != null && (resolved.kpi.value != null || resolved.kpi.label)) {
    if (![...out.keys()].some((key) => key.toLowerCase() === "value")) {
      const label =
        typeof resolved.kpi.label === "string" && resolved.kpi.label.trim()
          ? resolved.kpi.label.trim()
          : "value";
      put("value", label, true);
    }
  }
  for (const metric of resolved?.kpiMetrics ?? []) {
    if (metric.field) put(metric.field, metric.label || metric.field, true);
  }
  for (const col of resolved?.table?.columns ?? []) {
    if (col.key) put(col.key, col.label || col.key, true);
  }
  const firstRow = resolved?.table?.rows?.[0];
  if (firstRow && typeof firstRow === "object") {
    for (const key of Object.keys(firstRow)) {
      put(key, key, false);
    }
  }

  // Catálogo TV: só sobrescreve com rótulo curado (≠ chave / humanize fraco).
  for (const item of catalogFields ?? []) {
    const field = item.field.trim();
    if (!field) continue;
    const label = item.label.trim() || field;
    if (isCuratedLabel(field, label)) {
      put(field, label, true);
    } else if (!out.has(field)) {
      put(field, label, false);
    }
  }

  // fieldLabels do bloco data_source — override do usuário.
  if (sourceFieldLabels) {
    for (const [field, label] of Object.entries(sourceFieldLabels)) {
      const key = field.trim();
      if (!key || typeof label !== "string" || !label.trim()) continue;
      const existing = [...out.keys()].find((item) => item.toLowerCase() === key.toLowerCase());
      if (existing) {
        out.set(existing, label.trim());
      } else {
        out.set(key, label.trim());
      }
    }
  }

  return [...out.entries()].map(([field, label]) => ({ field, label }));
}

/** Sugere projeções iniciais ao conectar uma fonte (sem sobrescrever config existente). */
export function suggestDefaultProjections(
  resolved: ComunicadoDataResolved | undefined,
  fieldTypes?: Record<string, "number" | "string" | "date"> | null,
  chartType?: ComunicadoChartType | null,
): {
  kpiProjection?: KpiViewProjection;
  chartProjection?: ChartViewProjection;
  tableProjection?: TableViewProjection;
} {
  if (!resolved) return {};
  const fields = discoverResolvedFieldOptions(resolved);
  const typeOf = (field: string): "number" | "string" | "date" | undefined =>
    fieldTypes?.[field];
  const policy = resolveChartDataPolicy(chartType ?? "line");

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

  let chartProjection: ChartViewProjection | undefined;
  if (policy.chartType === "scatter" || policy.chartType === "bubble") {
    const xField = numericFields[0]?.field;
    const yField = numericFields[1]?.field ?? numericFields[0]?.field;
    if (xField && yField) {
      chartProjection = {
        categoryField: xField,
        series: [
          {
            field: yField,
            label: numericFields.find((item) => item.field === yField)?.label,
            aggregation: "first",
          },
          ...(policy.chartType === "bubble" && numericFields[2]
            ? [
                {
                  field: numericFields[2].field,
                  label: numericFields[2].label,
                  aggregation: "first" as const,
                },
              ]
            : []),
        ],
      };
    }
  } else if (policy.chartType === "histogram") {
    const measure = numericFields[0];
    if (measure) {
      chartProjection = {
        series: [
          {
            field: measure.field,
            label: measure.label,
            aggregation: "first",
          },
        ],
      };
    }
  } else if (policy.rowMode === "groupByCategory") {
    if (categoryCandidate) {
      const measure = numericFields[0];
      chartProjection = {
        categoryField: categoryCandidate,
        series: measure
          ? [
              {
                field: measure.field,
                label: measure.label,
                aggregation: policy.defaultAggregation,
              },
              ...numericFields.slice(1, policy.maxSeries).map((item) => ({
                field: item.field,
                label: item.label,
                aggregation: policy.defaultAggregation,
              })),
            ].slice(0, policy.maxSeries)
          : [
              {
                field: categoryCandidate,
                label: "Contagem",
                aggregation: "count" as const,
              },
            ],
      };
    }
  } else if (numericFields.length > 0) {
    chartProjection = {
      categoryField: categoryCandidate,
      series: numericFields.slice(0, policy.maxSeries).map((item) => ({
        field: item.field,
        label: item.label,
        aggregation: policy.defaultAggregation,
      })),
    };
  }

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
