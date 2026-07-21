/**
 * Registro de rótulos de display por fonte — chave da API estável; só muda o texto na TV.
 *
 * Cascata:
 *   1. label na projeção do visual
 *   2. data_source.fieldLabels[field]
 *   3. catálogo / resolved atual
 *   4. field (chave bruta)
 */

import type {
  ComunicadoDataResolved,
  ComunicadoDataTableColumn,
} from "./comunicadoTypes";

export type FieldLabelsMap = Record<string, string>;

export function normalizeFieldLabels(raw: unknown): FieldLabelsMap | undefined {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return undefined;
  const out: FieldLabelsMap = {};
  for (const [key, value] of Object.entries(raw as Record<string, unknown>)) {
    const field = String(key ?? "").trim();
    if (!field) continue;
    if (typeof value !== "string") continue;
    const label = value.trim();
    if (!label) continue;
    out[field] = label;
  }
  return Object.keys(out).length > 0 ? out : undefined;
}

export type ResolveFieldDisplayLabelInput = {
  field: string;
  projectionLabel?: string | null;
  sourceFieldLabels?: FieldLabelsMap | null;
  catalogLabel?: string | null;
  resolvedLabel?: string | null;
};

export function resolveFieldDisplayLabel(input: ResolveFieldDisplayLabelInput): string {
  const field = String(input.field ?? "").trim();
  if (!field) return "";
  const projection = input.projectionLabel?.trim();
  if (projection) return projection;
  const fromSource = input.sourceFieldLabels?.[field]?.trim();
  if (fromSource) return fromSource;
  const catalog = input.catalogLabel?.trim();
  if (catalog) return catalog;
  const resolved = input.resolvedLabel?.trim();
  if (resolved) return resolved;
  return field;
}

/**
 * Reaplica rótulos do registro da fonte em table.columns e kpiMetrics.
 * Não altera keys das rows nem valores — só display.
 */
export function applyFieldLabelsToResolved(
  resolved: ComunicadoDataResolved | undefined,
  fieldLabels: FieldLabelsMap | null | undefined,
): ComunicadoDataResolved | undefined {
  if (!resolved) return resolved;
  const labels = normalizeFieldLabels(fieldLabels);
  if (!labels) return resolved;

  let next: ComunicadoDataResolved = resolved;
  let changed = false;

  if (resolved.table?.columns?.length) {
    const columns: ComunicadoDataTableColumn[] = resolved.table.columns.map((col) => {
      const override = labels[col.key]?.trim();
      if (!override || override === col.label) return col;
      changed = true;
      return { ...col, label: override };
    });
    if (changed) {
      next = {
        ...next,
        table: { ...resolved.table, columns },
      };
    }
  }

  if (resolved.kpiMetrics?.length) {
    let metricsChanged = false;
    const kpiMetrics = resolved.kpiMetrics.map((metric) => {
      const override = labels[metric.field]?.trim();
      if (!override || override === metric.label) return metric;
      metricsChanged = true;
      return { ...metric, label: override };
    });
    if (metricsChanged) {
      changed = true;
      const primary = kpiMetrics[0];
      next = {
        ...next,
        kpiMetrics,
        kpi: next.kpi
          ? {
              ...next.kpi,
              label:
                (primary && labels[primary.field]?.trim()) ||
                next.kpi.label,
            }
          : next.kpi,
      };
    }
  }

  if (resolved.chart?.series?.length) {
    let seriesChanged = false;
    const series = resolved.chart.series.map((entry) => {
      const field = entry.field?.trim();
      if (!field) return entry;
      const override = labels[field]?.trim();
      if (!override || override === entry.name) return entry;
      seriesChanged = true;
      return { ...entry, name: override };
    });
    if (seriesChanged) {
      changed = true;
      next = {
        ...next,
        chart: { ...resolved.chart, series },
      };
    }
  }

  return changed ? next : resolved;
}

export type EditableFieldOption = {
  field: string;
  /** Rótulo efetivo atual (já resolvido). */
  label: string;
  /** Default sem o registro da fonte (catálogo/resolved). */
  defaultLabel: string;
};

/**
 * Campos editáveis: colunas da tabela + métricas KPI + keys do catálogo.
 */
export function suggestEditableFields(
  resolved: ComunicadoDataResolved | undefined,
  catalogFields?: Array<{ field: string; label: string }>,
  sourceFieldLabels?: FieldLabelsMap | null,
): EditableFieldOption[] {
  const defaults = new Map<string, string>();
  for (const item of catalogFields ?? []) {
    const field = item.field.trim();
    if (field) defaults.set(field, item.label.trim() || field);
  }
  for (const metric of resolved?.kpiMetrics ?? []) {
    if (metric.field && !defaults.has(metric.field)) {
      defaults.set(metric.field, metric.label || metric.field);
    }
  }
  for (const col of resolved?.table?.columns ?? []) {
    if (col.key && !defaults.has(col.key)) {
      defaults.set(col.key, col.label || col.key);
    }
  }
  const firstRow = resolved?.table?.rows?.[0];
  if (firstRow && typeof firstRow === "object") {
    for (const key of Object.keys(firstRow)) {
      if (!defaults.has(key)) defaults.set(key, key);
    }
  }

  return [...defaults.entries()].map(([field, defaultLabel]) => ({
    field,
    defaultLabel,
    label: resolveFieldDisplayLabel({
      field,
      sourceFieldLabels,
      catalogLabel: defaultLabel,
      resolvedLabel: defaultLabel,
    }),
  }));
}

/** Patch do mapa: vazio remove a entrada. */
export function patchFieldLabels(
  current: FieldLabelsMap | null | undefined,
  field: string,
  label: string | null | undefined,
): FieldLabelsMap | undefined {
  const key = field.trim();
  if (!key) return normalizeFieldLabels(current);
  const next: FieldLabelsMap = { ...(normalizeFieldLabels(current) ?? {}) };
  const trimmed = label?.trim() ?? "";
  if (!trimmed) {
    delete next[key];
  } else {
    next[key] = trimmed;
  }
  return Object.keys(next).length > 0 ? next : undefined;
}
